"""Unit tests for the ROS 2 message registry, its extension API and the converters."""

from __future__ import annotations

import numpy as np
import pytest
from dalaran.ros2 import msg_map
from dalaran.ros2.msg_map import (
    convert,
    lookup,
    marker_entity_path,
    normalize_type_name,
    register,
    registered_types,
    unregister,
)

from .fake_msgs import Simple, color, header, pose, quat, transform_stamped, vec3

# -- registry ---------------------------------------------------------------


@pytest.mark.parametrize(
    "spelling",
    ["sensor_msgs/Imu", "sensor_msgs/msg/Imu", "sensor_msgs.msg.Imu"],
)
def test_every_ros_type_name_spelling_resolves_to_the_same_entry(spelling: str) -> None:
    assert normalize_type_name(spelling) == "sensor_msgs/msg/Imu"
    assert lookup(spelling) is msg_map.convert_imu


def test_unparseable_type_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="Cannot parse"):
        normalize_type_name("Imu")


def test_the_built_in_messages_are_all_registered() -> None:
    expected = {
        "sensor_msgs/msg/PointCloud2",
        "sensor_msgs/msg/LaserScan",
        "sensor_msgs/msg/Image",
        "sensor_msgs/msg/CompressedImage",
        "sensor_msgs/msg/CameraInfo",
        "sensor_msgs/msg/Imu",
        "sensor_msgs/msg/JointState",
        "sensor_msgs/msg/NavSatFix",
        "nav_msgs/msg/Odometry",
        "nav_msgs/msg/Path",
        "nav_msgs/msg/OccupancyGrid",
        "geometry_msgs/msg/PoseStamped",
        "geometry_msgs/msg/TransformStamped",
        "geometry_msgs/msg/Twist",
        "geometry_msgs/msg/PoseArray",
        "tf2_msgs/msg/TFMessage",
        "visualization_msgs/msg/Marker",
        "visualization_msgs/msg/MarkerArray",
    }
    assert expected <= set(registered_types())


def test_unknown_types_resolve_to_nothing() -> None:
    assert lookup("nowhere_msgs/msg/Nothing") is None


def test_a_wildcard_covers_a_whole_package() -> None:
    # `std_msgs/msg/*` catches the types we did not enumerate individually.
    assert lookup("std_msgs/msg/Float32MultiArray") is msg_map.convert_std_msg


class TestExtensionApi:
    """The `@register` decorator is a documented, supported extension point."""

    def teardown_method(self) -> None:
        unregister("my_pkg/msg/BatteryPack")
        unregister("my_pkg/msg/Other")

    def test_a_custom_message_type_becomes_first_class(self, ctx, captured) -> None:
        @register("my_pkg/msg/BatteryPack")
        def log_battery(msg, entity_path, context) -> None:
            context.log(f"{entity_path}/charge", msg.charge)

        assert lookup("my_pkg/BatteryPack") is log_battery
        assert convert("my_pkg/msg/BatteryPack", Simple(charge=0.75), "battery", ctx)
        assert captured.logs[0].entity_path == "battery/charge"
        assert captured.logs[0].archetypes == (0.75,)

    def test_one_converter_can_serve_several_types(self) -> None:
        @register("my_pkg/msg/BatteryPack", "my_pkg/msg/Other")
        def log_anything(_msg, _entity_path, _context) -> None:
            pass

        assert lookup("my_pkg/msg/Other") is log_anything

    def test_registering_over_a_built_in_raises_by_default(self) -> None:
        with pytest.raises(ValueError, match="already registered"):

            @register("sensor_msgs/msg/Imu")
            def shadow(_msg, _entity_path, _context) -> None:
                pass

    def test_a_built_in_can_be_replaced_deliberately(self, ctx, captured) -> None:
        original = lookup("sensor_msgs/msg/Imu")
        try:

            @register("sensor_msgs/msg/Imu", override=True)
            def replacement(_msg, entity_path, context) -> None:
                context.log(entity_path, "mine")

            assert convert("sensor_msgs/Imu", None, "imu", ctx)
            assert captured.logs[0].archetypes == ("mine",)
        finally:
            register("sensor_msgs/msg/Imu", override=True)(original)

    def test_converting_an_unregistered_type_is_a_no_op(self, ctx, captured) -> None:
        assert not convert("nowhere_msgs/msg/Nothing", None, "x", ctx)
        assert captured.logs == []


# -- converters -------------------------------------------------------------


def test_laser_scan_becomes_points_in_the_sensor_frame(_fake_dl, ctx, captured) -> None:
    scan = Simple(
        header=header(frame_id="laser"),
        ranges=[1.0, 2.0, np.inf, 4.0],
        angle_min=0.0,
        angle_increment=np.pi / 2,
        range_min=0.0,
        range_max=100.0,
    )
    msg_map.convert_laser_scan(scan, "scan", ctx)

    points = captured.first("Points3D")
    positions = np.asarray(points.args[0])
    # The `inf` beam is dropped, and angle zero points forward.
    assert positions.shape == (3, 3)
    np.testing.assert_allclose(positions[0], [1.0, 0.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(positions[1], [0.0, 2.0, 0.0], atol=1e-6)


def test_imu_logs_orientation_arrows_and_per_axis_series(_fake_dl, ctx, captured) -> None:
    imu = Simple(
        header=header(frame_id="imu_link"),
        orientation=quat(0.0, 0.0, 0.0, 1.0),
        orientation_covariance=[0.01] + [0.0] * 8,
        linear_acceleration=vec3(0.0, 0.0, 9.81),
        angular_velocity=vec3(0.0, 0.0, 0.5),
    )
    msg_map.convert_imu(imu, "imu", ctx)

    assert "Transform3D" in captured.names()
    assert captured.by_path("imu/linear_acceleration/z")[0].args == (9.81,)
    assert captured.by_path("imu/angular_velocity/z")[0].args == (0.5,)


def test_imu_without_a_valid_orientation_logs_no_transform(_fake_dl, ctx, captured) -> None:
    imu = Simple(
        header=header(frame_id="imu_link"),
        orientation=quat(),
        orientation_covariance=[-1.0] + [0.0] * 8,  # the ROS "no orientation" marker
        linear_acceleration=vec3(),
        angular_velocity=vec3(),
    )
    msg_map.convert_imu(imu, "imu", ctx)
    assert "Transform3D" not in captured.names()


def test_joint_state_logs_one_series_per_joint_and_quantity(_fake_dl, ctx, captured) -> None:
    state = Simple(
        header=header(),
        name=["arm/shoulder", "elbow"],
        position=[0.1, 0.2],
        velocity=[1.0, 2.0],
        effort=[],
    )
    msg_map.convert_joint_state(state, "joints", ctx)

    # The `/` in a joint name must not create an extra entity level.
    assert captured.paths == [
        "joints/position/arm_shoulder",
        "joints/position/elbow",
        "joints/velocity/arm_shoulder",
        "joints/velocity/elbow",
    ]


def test_odometry_logs_a_transform_and_a_twist(_fake_dl, ctx, captured) -> None:
    odom = Simple(
        header=header(frame_id="odom"),
        pose=Simple(pose=pose(vec3(1.0, 2.0, 0.0))),
        twist=Simple(twist=Simple(linear=vec3(0.5, 0.0, 0.0), angular=vec3(0.0, 0.0, 0.25))),
    )
    msg_map.convert_odometry(odom, "odom", ctx)

    transform = captured.first("Transform3D")
    np.testing.assert_allclose(transform.kwargs["translation"], [1.0, 2.0, 0.0])
    assert captured.by_path("odom/linear_velocity/x")[0].args == (0.5,)


def test_nav_sat_fix_without_a_fix_is_skipped(_fake_dl, ctx, captured) -> None:
    fix = Simple(status=Simple(status=-1), latitude=0.0, longitude=0.0, altitude=0.0)
    msg_map.convert_nav_sat_fix(fix, "gps", ctx)
    assert captured.logs == []


def test_nav_sat_fix_with_a_fix_becomes_geo_points(_fake_dl, ctx, captured) -> None:
    fix = Simple(status=Simple(status=0), latitude=59.33, longitude=18.06, altitude=12.0)
    msg_map.convert_nav_sat_fix(fix, "gps", ctx)
    np.testing.assert_allclose(captured.first("GeoPoints").kwargs["lat_lon"], [[59.33, 18.06]])


def test_occupancy_grid_becomes_a_native_grid_map(_fake_dl, ctx, captured) -> None:
    grid = Simple(
        header=header(frame_id="map"),
        info=Simple(
            width=2,
            height=2,
            resolution=0.05,
            origin=pose(vec3(-1.0, -1.0, 0.0)),
        ),
        data=[0, 100, -1, 0],
    )
    msg_map.convert_occupancy_grid(grid, "map", ctx)

    grid_map = captured.first("GridMap")
    assert grid_map.kwargs["cell_size"] == pytest.approx(0.05)
    np.testing.assert_allclose(grid_map.kwargs["translation"], [-1.0, -1.0, 0.0])
    # Buffer row 0 is the top row, i.e. the message's last row.
    assert grid_map.kwargs["data"] == bytes([255, 0, 0, 100])
    assert grid_map.kwargs["colormap"] == "Colormap.RvizMap"


def test_tf_messages_drive_the_shared_transform_tree(_fake_dl, ctx) -> None:
    tf = Simple(
        transforms=[
            transform_stamped("odom", "base_link", translation=(1.0, 0.0, 0.0)),
            transform_stamped("base_link", "lidar", translation=(0.0, 0.0, 0.3)),
        ]
    )
    msg_map.convert_tf_message(tf, "tf", ctx)

    # Frames nest into an entity hierarchy, so the viewer composes the chain.
    assert ctx.frame_entity_paths["lidar"].endswith("odom/base_link/lidar")
    # And the tree can answer tf2-style questions about what it has seen.
    np.testing.assert_allclose(ctx.tree.lookup("odom", "lidar")[:3, 3], [1.0, 0.0, 0.3])


def test_tf_static_is_logged_as_static_data(_fake_dl, ctx, captured) -> None:
    tf = Simple(transforms=[transform_stamped("base_link", "lidar")])
    msg_map.convert_tf_message(tf, "tf_static", ctx)
    assert captured.logs[0].static is True


def test_sensor_data_lands_on_its_tf_frame_once_tf_is_known(_fake_dl, ctx, captured) -> None:
    msg_map.convert_tf_message(Simple(transforms=[transform_stamped("base_link", "laser")]), "tf", ctx)
    captured.logs.clear()

    scan = Simple(
        header=header(frame_id="laser"),
        ranges=[1.0],
        angle_min=0.0,
        angle_increment=0.1,
        range_min=0.0,
        range_max=10.0,
    )
    msg_map.convert_laser_scan(scan, "scan", ctx)
    # Not "scan": the scan belongs on the frame it was measured in.
    assert captured.logs[0].entity_path.endswith("base_link/laser")


def test_marker_entity_paths_are_namespaced_by_ns_and_id() -> None:
    assert marker_entity_path(Simple(ns="obstacles", id=7), "markers") == "markers/obstacles/7"
    assert marker_entity_path(Simple(ns="", id=0), "markers") == "markers/default/0"


def test_a_delete_all_marker_clears_the_subtree(_fake_dl, ctx, captured) -> None:
    msg_map.convert_marker(Simple(action=3, ns="obstacles", id=0), "markers", ctx)
    assert captured.first("Clear").kwargs == {"recursive": True}
    assert captured.logs[0].entity_path == "markers"


def test_a_sphere_marker_becomes_an_ellipsoid(_fake_dl, ctx, captured) -> None:
    marker = Simple(
        action=0,
        type=2,
        ns="obstacles",
        id=3,
        pose=pose(vec3(1.0, 2.0, 3.0)),
        scale=vec3(0.4, 0.4, 0.4),
        color=color(1.0, 0.0, 0.0, 1.0),
        points=[],
        colors=[],
    )
    msg_map.convert_marker(marker, "markers", ctx)

    ellipsoid = captured.first("Ellipsoids3D")
    np.testing.assert_allclose(ellipsoid.kwargs["half_sizes"], [[0.2, 0.2, 0.2]])
    assert ellipsoid.kwargs["colors"] == [(255, 0, 0, 255)]
    assert captured.logs[0].entity_path == "markers/obstacles/3"


def test_a_line_list_marker_becomes_one_strip_per_segment(_fake_dl, ctx, captured) -> None:
    marker = Simple(
        action=0,
        type=5,
        ns="lines",
        id=1,
        pose=pose(),
        scale=vec3(0.01, 0.0, 0.0),
        color=color(0.0, 1.0, 0.0, 1.0),
        points=[vec3(0, 0, 0), vec3(1, 0, 0), vec3(1, 0, 0), vec3(1, 1, 0)],
        colors=[],
    )
    msg_map.convert_marker(marker, "markers", ctx)
    strips = captured.first("LineStrips3D").args[0]
    assert len(strips) == 2


def test_a_marker_array_logs_every_marker(_fake_dl, ctx, captured) -> None:
    def sphere(index: int) -> Simple:
        return Simple(
            action=0,
            type=2,
            ns="swarm",
            id=index,
            pose=pose(),
            scale=vec3(0.1, 0.1, 0.1),
            color=color(0.0, 0.0, 1.0, 1.0),
            points=[],
            colors=[],
        )

    msg_map.convert_marker_array(Simple(markers=[sphere(0), sphere(1)]), "markers", ctx)
    assert captured.paths == ["markers/swarm/0", "markers/swarm/1"]


@pytest.mark.parametrize(
    ("data", "expected"),
    [(True, 1.0), (3, 3.0), (2.5, 2.5)],
)
def test_std_msgs_scalars_become_scalar_series(_fake_dl, ctx, captured, data, expected) -> None:
    msg_map.convert_std_msg(Simple(data=data), "battery", ctx)
    assert captured.first("Scalars").args == (expected,)


def test_std_msgs_strings_become_text_logs(_fake_dl, ctx, captured) -> None:
    msg_map.convert_std_msg(Simple(data="all systems nominal"), "status", ctx)
    assert captured.first("TextLog").args == ("all systems nominal",)


def test_std_msgs_arrays_become_a_scalar_batch(_fake_dl, ctx, captured) -> None:
    msg_map.convert_std_msg(Simple(data=[1.0, 2.0, 3.0]), "cells", ctx)
    np.testing.assert_allclose(captured.first("Scalars").args[0], [1.0, 2.0, 3.0])
