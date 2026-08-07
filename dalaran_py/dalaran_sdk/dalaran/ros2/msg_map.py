"""
The registry that maps ROS 2 message types onto Dalaran archetypes.

Every entry is a converter function with the signature
`(msg, entity_path, ctx) -> None` that turns one ROS message into one or more
[`dalaran.log`][] calls. The built-in entries cover the messages a robot
actually publishes - point clouds, scans, images, transforms, odometry, maps,
markers - but the interesting part is that the registry is *open*:

```python
from dalaran.ros2 import register

@register("my_pkg/msg/BatteryPack")
def log_battery(msg, entity_path, ctx):
    for index, cell in enumerate(msg.cell_voltages):
        ctx.log(f"{entity_path}/cell{index}", dl.Scalars(cell))
```

Once registered, your message type is a first-class citizen everywhere: the live
[`Ros2Bridge`][dalaran.ros2.Ros2Bridge], the offline rosbag2 replayer and the
`dalaran-ros2` command line tool all go through this same table. You never have
to fork the bridge to support your own interfaces.

Message type names are accepted in every spelling ROS uses:
`"sensor_msgs/Imu"`, `"sensor_msgs/msg/Imu"` and `"sensor_msgs.msg.Imu"` all
refer to the same entry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterable, Sequence

import numpy as np

from .image import compressed_image_media_type, decode_image
from .naming import entity_path_join, sanitize_path_part
from .occupancy_grid import occupancy_grid_placement
from .pointcloud2 import decode_pointcloud2

if TYPE_CHECKING:
    import numpy.typing as npt

    from .context import Context

__all__ = [
    "Converter",
    "convert",
    "lookup",
    "normalize_type_name",
    "register",
    "registered_types",
    "unregister",
]

Converter = Callable[[Any, str, "Context"], None]

_REGISTRY: dict[str, Converter] = {}

# Marker fallback color, matching RViz's "you forgot to set a color" magenta.
_DEFAULT_COLOR = (255, 0, 255, 255)


def normalize_type_name(type_name: str) -> str:
    """
    Normalize a ROS 2 type name to the canonical `pkg/msg/Type` spelling.

    Examples
    --------
    ```python
    from dalaran.ros2 import normalize_type_name

    assert normalize_type_name("sensor_msgs/Imu") == "sensor_msgs/msg/Imu"
    assert normalize_type_name("sensor_msgs.msg.Imu") == "sensor_msgs/msg/Imu"
    assert normalize_type_name("sensor_msgs/msg/Imu") == "sensor_msgs/msg/Imu"
    ```

    """
    parts = [part for part in type_name.replace(".", "/").split("/") if part]
    if len(parts) == 2:
        package, name = parts
        return f"{package}/msg/{name}"
    if len(parts) == 3:
        return "/".join(parts)
    msg = f"Cannot parse ROS message type name {type_name!r}"
    raise ValueError(msg)


def register(*type_names: str, override: bool = False) -> Callable[[Converter], Converter]:
    """
    Register a converter for one or more ROS 2 message types.

    This is the extension point that makes `dalaran.ros2` work with *your*
    interfaces. The decorated function is called once per message, with the
    message, the entity path the topic maps to, and the
    [`Context`][dalaran.ros2.Context] to log through. It must not import `rclpy`
    at module scope, and it should log through `ctx.log` rather than
    [`dalaran.log`][] so that it stays testable and honors the caller's recording.

    Parameters
    ----------
    type_names:
        The message types to handle, in any accepted spelling.
    override:
        Set to `True` to deliberately replace an existing converter. Without it,
        registering over a built-in raises, so a typo cannot silently disable a
        message type.

    Returns
    -------
    collections.abc.Callable
        The decorator, which returns the converter unchanged so it stays
        directly callable and testable.

    Examples
    --------
    ```python
    import dalaran as dl
    from dalaran.ros2 import lookup, register


    @register("my_pkg/msg/BatteryPack")
    def log_battery(msg, entity_path, ctx):
        ctx.log(f"{entity_path}/state_of_charge", dl.Scalars(msg.state_of_charge))


    assert lookup("my_pkg/BatteryPack") is log_battery
    ```

    """

    def decorator(converter: Converter) -> Converter:
        for raw in type_names:
            key = normalize_type_name(raw)
            if key in _REGISTRY and not override:
                msg = (
                    f"A converter for {key!r} is already registered "
                    f"({_REGISTRY[key].__name__}); pass override=True if that is intentional"
                )
                raise ValueError(msg)
            _REGISTRY[key] = converter
        return converter

    return decorator


def unregister(type_name: str) -> Converter | None:
    """Remove and return the converter for `type_name`, or `None` if there was none."""
    return _REGISTRY.pop(normalize_type_name(type_name), None)


def lookup(type_name: str) -> Converter | None:
    """
    Return the converter registered for `type_name`, or `None`.

    Falls back to a `pkg/msg/*` wildcard entry, which is how the whole of
    `std_msgs` is covered by a single converter.

    Examples
    --------
    ```python
    from dalaran.ros2 import lookup

    assert lookup("sensor_msgs/PointCloud2") is not None
    assert lookup("nowhere_msgs/msg/Nothing") is None
    ```

    """
    key = normalize_type_name(type_name)
    converter = _REGISTRY.get(key)
    if converter is not None:
        return converter
    package = key.split("/", 1)[0]
    return _REGISTRY.get(f"{package}/msg/*")


def registered_types() -> list[str]:
    """Return every registered message type, sorted."""
    return sorted(_REGISTRY)


def convert(type_name: str, msg: Any, entity_path: str, ctx: Context) -> bool:
    """
    Convert and log one message, returning whether a converter was found.

    Examples
    --------
    ```python
    from dalaran.ros2 import convert
    from dalaran.ros2.context import Context

    captured: list = []
    assert not convert("nowhere_msgs/msg/Nothing", None, "x", Context(sink=captured.append))
    ```

    """
    converter = lookup(type_name)
    if converter is None:
        return False
    converter(msg, entity_path, ctx)
    return True


# -- small accessors over ROS's nested message structs ---------------------


def _xyz(point: Any) -> npt.NDArray[np.float64]:
    return np.array([point.x, point.y, point.z], dtype=np.float64)


def _xyzw(quaternion: Any) -> npt.NDArray[np.float64]:
    return np.array([quaternion.x, quaternion.y, quaternion.z, quaternion.w], dtype=np.float64)


def _pose(pose: Any) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    return _xyz(pose.position), _xyzw(pose.orientation)


def _points(points: Iterable[Any]) -> npt.NDArray[np.float32]:
    listed = list(points)
    if not listed:
        return np.zeros((0, 3), dtype=np.float32)
    return np.array([[p.x, p.y, p.z] for p in listed], dtype=np.float32)


def _color(color: Any) -> tuple[int, int, int, int]:
    return (
        int(round(float(color.r) * 255.0)),
        int(round(float(color.g) * 255.0)),
        int(round(float(color.b) * 255.0)),
        int(round(float(color.a) * 255.0)),
    )


def _frame_id(msg: Any) -> str:
    header = getattr(msg, "header", None)
    return str(getattr(header, "frame_id", "") or "").lstrip("/")


# -- sensor_msgs ------------------------------------------------------------


@register("sensor_msgs/msg/PointCloud2")
def convert_pointcloud2(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/PointCloud2` as [`dalaran.Points3D`][].

    Packed `rgb` colors are used when present; otherwise the cloud is colormapped
    by `intensity`, falling back to plain white. See
    [`dalaran.ros2.pointcloud2`][] for the layouts this handles.
    """
    import dalaran as dl

    cloud = decode_pointcloud2(msg)
    colors: Any = cloud.colors
    if colors is None and cloud.intensity is not None:
        from dalaran.robot import colormap_scalars

        colors = colormap_scalars(cloud.intensity)

    path = ctx.frame_path(cloud.frame_id, entity_path)
    ctx.log(path, dl.Points3D(cloud.positions, colors=colors, radii=0.02))


@register("sensor_msgs/msg/LaserScan")
def convert_laser_scan(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/LaserScan` as [`dalaran.Points3D`][] in the sensor frame.

    The projection goes through [`dalaran.robot.log_lidar_scan`][], so a scan
    logged by the bridge is identical to one logged by hand with the robot API,
    including the REP-103 angle convention and the dropping of `inf` beams.
    """
    from dalaran.robot import log_lidar_scan

    path = ctx.frame_path(_frame_id(msg), entity_path)
    if ctx.sink is not None:
        # Under a capturing sink we must not touch the global recording, so
        # reproduce the same archetype without going through the logging helper.
        import dalaran as dl
        from dalaran.robot import colormap_scalars, laser_scan_to_points

        points = laser_scan_to_points(
            msg.ranges,
            angle_min=float(msg.angle_min),
            angle_increment=float(msg.angle_increment),
            range_min=float(getattr(msg, "range_min", 0.0)),
            range_max=float(getattr(msg, "range_max", float("inf"))),
        )
        colors = colormap_scalars(np.linalg.norm(points, axis=1)) if len(points) else None
        ctx.log(path, dl.Points3D(points, colors=colors, radii=0.02))
        return

    log_lidar_scan(
        path,
        msg.ranges,
        angle_min=float(msg.angle_min),
        angle_increment=float(msg.angle_increment),
        range_min=float(getattr(msg, "range_min", 0.0)),
        range_max=float(getattr(msg, "range_max", float("inf"))),
        colorize_by_range=True,
        recording=ctx.recording,
    )


@register("sensor_msgs/msg/Image")
def convert_image(msg: Any, entity_path: str, ctx: Context) -> None:
    """Log a `sensor_msgs/Image` as an [`dalaran.Image`][] or [`dalaran.DepthImage`][]."""
    import dalaran as dl

    decoded = decode_image(
        msg.data,
        width=int(msg.width),
        height=int(msg.height),
        encoding=str(msg.encoding),
        step=int(getattr(msg, "step", 0)) or None,
        is_bigendian=bool(getattr(msg, "is_bigendian", False)),
    )
    path = ctx.frame_path(_frame_id(msg), entity_path)
    if decoded.kind == "depth":
        ctx.log(path, dl.DepthImage(decoded.array, meter=decoded.depth_meter))
    else:
        ctx.log(path, dl.Image(decoded.array))


@register("sensor_msgs/msg/CompressedImage")
def convert_compressed_image(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/CompressedImage` as [`dalaran.EncodedImage`][].

    The compressed bytes are forwarded untouched, so no JPEG decoder is needed
    on the bridge host and the recording stays small.
    """
    import dalaran as dl

    path = ctx.frame_path(_frame_id(msg), entity_path)
    ctx.log(
        path,
        dl.EncodedImage(
            contents=bytes(msg.data),
            media_type=compressed_image_media_type(str(msg.format)),
        ),
    )


@register("sensor_msgs/msg/CameraInfo")
def convert_camera_info(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/CameraInfo` as a [`dalaran.Pinhole`][] in an RDF optical frame.

    The message's `k` matrix already describes the rectified pinhole in the
    optical (x right, y down, z forward) convention, so it is used verbatim.
    """
    import dalaran as dl

    intrinsics = np.asarray(getattr(msg, "k", getattr(msg, "K", ())), dtype=np.float64).reshape(3, 3)
    path = ctx.frame_path(_frame_id(msg), entity_path)
    ctx.log(
        path,
        dl.Pinhole(
            image_from_camera=intrinsics,
            resolution=[int(msg.width), int(msg.height)],
            camera_xyz=dl.ViewCoordinates.RDF,
        ),
    )


@register("sensor_msgs/msg/Imu")
def convert_imu(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/Imu` as arrows plus per-axis time series.

    Orientation, when the driver provides one (`orientation_covariance[0] >= 0`),
    is logged as the IMU entity's transform.
    """
    import dalaran as dl

    path = ctx.frame_path(_frame_id(msg), entity_path)
    accel = _xyz(msg.linear_acceleration)
    gyro = _xyz(msg.angular_velocity)

    covariance = np.asarray(getattr(msg, "orientation_covariance", (0.0,)), dtype=np.float64).reshape(-1)
    has_orientation = covariance.size == 0 or covariance[0] >= 0.0
    if has_orientation:
        quaternion = _xyzw(msg.orientation)
        if np.linalg.norm(quaternion) > 0.0:
            ctx.log(path, dl.Transform3D(quaternion=quaternion))

    for name, vector, scale, color in (
        ("linear_acceleration", accel, 0.1, (255, 100, 60)),
        ("angular_velocity", gyro, 1.0, (60, 160, 255)),
    ):
        ctx.log(
            f"{path}/{name}",
            dl.Arrows3D(vectors=[vector * scale], origins=[[0.0, 0.0, 0.0]], colors=[color]),
        )
        for axis, component in zip("xyz", vector):
            ctx.log(f"{path}/{name}/{axis}", dl.Scalars(float(component)))


@register("sensor_msgs/msg/JointState")
def convert_joint_state(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/JointState` as one scalar series per joint and quantity.

    Positions, velocities and efforts are each optional in the message, and any
    that are present land under `<entity_path>/<quantity>/<joint>`.
    """
    import dalaran as dl

    names = [sanitize_path_part(str(name)) for name in msg.name]
    for quantity in ("position", "velocity", "effort"):
        values = list(getattr(msg, quantity, ()) or ())
        for name, value in zip(names, values):
            ctx.log(f"{entity_path}/{quantity}/{name}", dl.Scalars(float(value)))


@register("sensor_msgs/msg/NavSatFix")
def convert_nav_sat_fix(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `sensor_msgs/NavSatFix` as a [`dalaran.GeoPoints`][] on the map view.

    Messages with `status.status < 0` (`STATUS_NO_FIX`) are skipped rather than
    logged at latitude/longitude zero.
    """
    import dalaran as dl

    status = getattr(getattr(msg, "status", None), "status", 0)
    if int(status) < 0:
        return
    ctx.log(entity_path, dl.GeoPoints(lat_lon=[[float(msg.latitude), float(msg.longitude)]]))
    ctx.log(f"{entity_path}/altitude", dl.Scalars(float(msg.altitude)))


# -- nav_msgs ---------------------------------------------------------------


@register("nav_msgs/msg/Odometry")
def convert_odometry(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `nav_msgs/Odometry` as a pose plus body-frame twist time series.

    The pose is logged as the entity's own [`dalaran.Transform3D`][], so any
    sensor data parented below it moves with the robot.
    """
    import dalaran as dl

    translation, quaternion = _pose(msg.pose.pose)
    ctx.log(entity_path, dl.Transform3D(translation=translation, quaternion=quaternion))

    twist = msg.twist.twist
    for name, vector in (("linear_velocity", _xyz(twist.linear)), ("angular_velocity", _xyz(twist.angular))):
        for axis, component in zip("xyz", vector):
            ctx.log(f"{entity_path}/{name}/{axis}", dl.Scalars(float(component)))


@register("nav_msgs/msg/Path")
def convert_path(msg: Any, entity_path: str, ctx: Context) -> None:
    """Log a `nav_msgs/Path` as a single [`dalaran.LineStrips3D`][] strip."""
    import dalaran as dl

    positions = np.array(
        [[p.pose.position.x, p.pose.position.y, p.pose.position.z] for p in msg.poses],
        dtype=np.float32,
    ).reshape(-1, 3)
    path = ctx.frame_path(_frame_id(msg), entity_path)
    ctx.log(path, dl.LineStrips3D([positions], colors=[(60, 200, 120)], radii=0.02))


@register("nav_msgs/msg/OccupancyGrid")
def convert_occupancy_grid(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `nav_msgs/OccupancyGrid` as a native [`dalaran.GridMap`][].

    Using `GridMap` rather than a flat image is what gets you the viewer's
    grid-map visualizer, world-space cell sizing from `info.resolution`, and the
    map's `info.origin` pose applied to its lower-left corner. Unknown cells keep
    their ROS byte value of `255`, which
    [`dalaran.components.Colormap.RvizMap`][] renders in its own distinct color.
    """
    import dalaran as dl

    info = msg.info
    origin_position, origin_orientation = _pose(info.origin)
    placement = occupancy_grid_placement(
        msg.data,
        width=info.width,
        height=info.height,
        resolution=info.resolution,
        origin_translation=origin_position,
        origin_quaternion=origin_orientation,
        frame_id=_frame_id(msg),
    )
    ctx.log(
        entity_path,
        dl.GridMap(
            data=placement.cells.tobytes(),
            format=dl.components.ImageFormat(
                width=placement.width,
                height=placement.height,
                color_model="L",
                channel_datatype="U8",
            ),
            cell_size=placement.cell_size,
            translation=placement.translation,
            quaternion=placement.quaternion,
            colormap=dl.components.Colormap.RvizMap,
        ),
    )


# -- geometry_msgs ----------------------------------------------------------


@register("geometry_msgs/msg/PoseStamped")
def convert_pose_stamped(msg: Any, entity_path: str, ctx: Context) -> None:
    """Log a `geometry_msgs/PoseStamped` as the entity's [`dalaran.Transform3D`][]."""
    import dalaran as dl

    translation, quaternion = _pose(msg.pose)
    ctx.log(entity_path, dl.Transform3D(translation=translation, quaternion=quaternion))


@register("geometry_msgs/msg/PoseArray")
def convert_pose_array(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `geometry_msgs/PoseArray` as points plus heading arrows.

    Particle filters publish these by the thousand, so the heading is drawn as a
    short arrow along each pose's local +x rather than as a full transform.
    """
    import dalaran as dl

    from dalaran.robot._math import quaternion_to_matrix

    poses = list(msg.poses)
    positions = np.array([[p.position.x, p.position.y, p.position.z] for p in poses], dtype=np.float32).reshape(-1, 3)
    headings = np.array(
        [quaternion_to_matrix(_xyzw(p.orientation))[:, 0] * 0.2 for p in poses],
        dtype=np.float32,
    ).reshape(-1, 3)

    ctx.log(entity_path, dl.Points3D(positions, radii=0.03, colors=[(255, 200, 60)]))
    ctx.log(f"{entity_path}/heading", dl.Arrows3D(vectors=headings, origins=positions, colors=[(255, 200, 60)]))


@register("geometry_msgs/msg/Twist", "geometry_msgs/msg/TwistStamped")
def convert_twist(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `geometry_msgs/Twist` as body-frame arrows plus per-axis time series.

    `TwistStamped` is handled by the same converter; the inner `twist` is
    unwrapped automatically.
    """
    import dalaran as dl

    twist = getattr(msg, "twist", msg)
    linear = _xyz(twist.linear)
    angular = _xyz(twist.angular)

    ctx.log(
        f"{entity_path}/linear",
        dl.Arrows3D(vectors=[linear], origins=[[0.0, 0.0, 0.0]], colors=[(80, 220, 255)]),
    )
    ctx.log(
        f"{entity_path}/angular",
        dl.Arrows3D(vectors=[angular], origins=[[0.0, 0.0, 0.0]], colors=[(255, 140, 80)]),
    )
    for name, vector in (("linear", linear), ("angular", angular)):
        for axis, component in zip("xyz", vector):
            ctx.log(f"{entity_path}/{name}/{axis}", dl.Scalars(float(component)))


# -- tf2_msgs ---------------------------------------------------------------


def apply_transform_stamped(transform: Any, ctx: Context, *, static: bool = False) -> str:
    """
    Feed one `geometry_msgs/TransformStamped` into the context's transform tree.

    The tf tree is discovered as it streams: frames are declared on the fly the
    first time they are mentioned, and the resulting entity path is remembered in
    `ctx.frame_entity_paths` so sensor data can be placed on the frame it was
    measured in.

    Parameters
    ----------
    transform:
        A `geometry_msgs/TransformStamped`, i.e. one element of a `/tf` message.
    ctx:
        The context whose transform tree and frame table to update.
    static:
        Log the transform as static data. `/tf_static` sets this.

    Returns
    -------
    str
        The entity path the transform was logged to.

    """
    tree = ctx.tree
    parent = str(transform.header.frame_id).lstrip("/") or tree.root
    child = str(transform.child_frame_id).lstrip("/")

    if parent not in tree:
        # A tf tree can be published parent-first or child-first; attach unknown
        # parents to the root and let the real transform arrive later.
        tree.add(parent, tree.root if parent != tree.root else None)
        ctx.frame_entity_paths[parent] = tree.entity_path(parent)

    translation = _xyz(transform.transform.translation)
    quaternion = _xyzw(transform.transform.rotation)

    if ctx.sink is not None:
        tree.set(child, parent=parent, translation=translation, quaternion=quaternion, log=False)
        path = tree.entity_path(child)
        ctx.frame_entity_paths[child] = path

        import dalaran as dl

        ctx.log(path, dl.Transform3D(translation=translation, quaternion=quaternion), static=static)
        return path

    tree.set(child, parent=parent, translation=translation, quaternion=quaternion, static=static)
    path = tree.entity_path(child)
    ctx.frame_entity_paths[child] = path
    return path


@register("tf2_msgs/msg/TFMessage")
def convert_tf_message(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Replay a `tf2_msgs/TFMessage` into the context's [`dalaran.robot.TransformTree`][].

    `/tf` is handled specially on purpose: rather than logging transforms at the
    topic's own entity path, each transform is placed on the entity that its
    child frame owns, which is what makes the whole recording share one coherent
    transform hierarchy.
    """
    static = entity_path.rstrip("/").endswith("tf_static")
    for transform in msg.transforms:
        apply_transform_stamped(transform, ctx, static=static)


@register("geometry_msgs/msg/TransformStamped")
def convert_transform_stamped(msg: Any, entity_path: str, ctx: Context) -> None:
    """Feed a bare `geometry_msgs/TransformStamped` into the transform tree."""
    apply_transform_stamped(msg, ctx)


# -- visualization_msgs -----------------------------------------------------

# `visualization_msgs/Marker` type constants.
_ARROW, _CUBE, _SPHERE, _CYLINDER = 0, 1, 2, 3
_LINE_STRIP, _LINE_LIST, _CUBE_LIST, _SPHERE_LIST, _POINTS = 4, 5, 6, 7, 8
_TEXT_VIEW_FACING, _MESH_RESOURCE, _TRIANGLE_LIST = 9, 10, 11

# `visualization_msgs/Marker` action constants.
_ADD, _MODIFY, _DELETE, _DELETE_ALL = 0, 1, 2, 3


def marker_entity_path(msg: Any, base: str) -> str:
    """
    Return the entity path a marker belongs on: `<base>/<namespace>/<id>`.

    Markers are identified by an `(ns, id)` pair, and RViz expects a later
    marker with the same pair to replace the earlier one. Giving each pair its
    own entity gets exactly that behaviour for free.

    Examples
    --------
    ```python
    from dalaran.ros2.msg_map import marker_entity_path


    class Marker:
        ns, id = "obstacles", 7


    assert marker_entity_path(Marker(), "markers") == "markers/obstacles/7"
    ```

    """
    namespace = sanitize_path_part(str(getattr(msg, "ns", "") or "")) or "default"
    return entity_path_join(base, namespace, str(int(getattr(msg, "id", 0))))


def _marker_colors(msg: Any, count: int) -> Sequence[tuple[int, int, int, int]]:
    per_point = list(getattr(msg, "colors", ()) or ())
    if per_point:
        return [_color(color) for color in per_point]
    color = _color(msg.color) if hasattr(msg, "color") else _DEFAULT_COLOR
    if color[3] == 0:
        # An all-zero ColorRGBA means "the publisher forgot"; RViz shows magenta.
        color = _DEFAULT_COLOR
    return [color] * max(count, 1)


@register("visualization_msgs/msg/Marker")
def convert_marker(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log a `visualization_msgs/Marker` as the matching Dalaran archetype.

    Each `(ns, id)` pair gets its own entity, so `DELETE` and `DELETEALL`
    actions map cleanly onto [`dalaran.Clear`][].
    """
    import dalaran as dl

    action = int(getattr(msg, "action", _ADD))
    if action == _DELETE_ALL:
        ctx.log(entity_path, dl.Clear(recursive=True))
        return

    path = marker_entity_path(msg, entity_path)
    if action == _DELETE:
        ctx.log(path, dl.Clear(recursive=True))
        return
    if action not in (_ADD, _MODIFY):
        return

    marker_type = int(getattr(msg, "type", _POINTS))
    center, quaternion = _pose(msg.pose)
    scale = _xyz(msg.scale)
    points = _points(getattr(msg, "points", ()) or ())

    if marker_type == _ARROW:
        if len(points) >= 2:
            ctx.log(
                path,
                dl.Arrows3D(
                    vectors=[points[1] - points[0]],
                    origins=[points[0]],
                    colors=_marker_colors(msg, 1),
                ),
            )
        else:
            from dalaran.robot._math import quaternion_to_matrix

            direction = quaternion_to_matrix(quaternion)[:, 0] * float(scale[0])
            ctx.log(path, dl.Arrows3D(vectors=[direction], origins=[center], colors=_marker_colors(msg, 1)))
    elif marker_type in (_CUBE, _CUBE_LIST):
        centers = points if marker_type == _CUBE_LIST and len(points) else np.array([center], dtype=np.float32)
        quaternions = None if marker_type == _CUBE_LIST else [quaternion]
        ctx.log(
            path,
            dl.Boxes3D(
                sizes=np.tile(scale, (len(centers), 1)),
                centers=centers,
                quaternions=quaternions,
                colors=_marker_colors(msg, len(centers)),
            ),
        )
    elif marker_type in (_SPHERE, _SPHERE_LIST):
        centers = points if marker_type == _SPHERE_LIST and len(points) else np.array([center], dtype=np.float32)
        ctx.log(
            path,
            dl.Ellipsoids3D(
                half_sizes=np.tile(scale / 2.0, (len(centers), 1)),
                centers=centers,
                colors=_marker_colors(msg, len(centers)),
            ),
        )
    elif marker_type == _CYLINDER:
        ctx.log(
            path,
            dl.Cylinders3D(
                lengths=[float(scale[2])],
                radii=[float(scale[0]) / 2.0],
                centers=[center],
                quaternions=[quaternion],
                colors=_marker_colors(msg, 1),
            ),
        )
    elif marker_type == _LINE_STRIP:
        ctx.log(path, dl.LineStrips3D([points], radii=float(scale[0]), colors=_marker_colors(msg, 1)))
    elif marker_type == _LINE_LIST:
        strips = points[: len(points) // 2 * 2].reshape(-1, 2, 3)
        ctx.log(path, dl.LineStrips3D(list(strips), radii=float(scale[0]), colors=_marker_colors(msg, len(strips))))
    elif marker_type == _POINTS:
        ctx.log(path, dl.Points3D(points, radii=float(scale[0]) / 2.0, colors=_marker_colors(msg, len(points))))
    elif marker_type == _TEXT_VIEW_FACING:
        ctx.log(
            path,
            dl.Points3D(
                [center],
                radii=0.0,
                labels=[str(getattr(msg, "text", ""))],
                show_labels=True,
                colors=_marker_colors(msg, 1),
            ),
        )
    elif marker_type == _TRIANGLE_LIST:
        ctx.log(path, dl.Mesh3D(vertex_positions=points, vertex_colors=_marker_colors(msg, len(points))))
    elif marker_type == _MESH_RESOURCE:
        resource = str(getattr(msg, "mesh_resource", ""))
        if resource.startswith("file://"):
            ctx.log(path, dl.Asset3D(path=resource[len("file://") :]))
        ctx.log(path, dl.Transform3D(translation=center, quaternion=quaternion, scale=scale))


@register("visualization_msgs/msg/MarkerArray")
def convert_marker_array(msg: Any, entity_path: str, ctx: Context) -> None:
    """Log every marker in a `visualization_msgs/MarkerArray`."""
    for marker in msg.markers:
        convert_marker(marker, entity_path, ctx)


# -- std_msgs ---------------------------------------------------------------

_STD_SCALAR_TYPES = (
    "Bool",
    "Byte",
    "Char",
    "Float32",
    "Float64",
    "Int8",
    "Int16",
    "Int32",
    "Int64",
    "UInt8",
    "UInt16",
    "UInt32",
    "UInt64",
)


@register("std_msgs/msg/*", *(f"std_msgs/msg/{name}" for name in _STD_SCALAR_TYPES))
def convert_std_msg(msg: Any, entity_path: str, ctx: Context) -> None:
    """
    Log any `std_msgs` message: numbers become scalars, everything else becomes text.

    This is registered under the `std_msgs/msg/*` wildcard as well as the
    individual numeric types, which is the pattern to copy if you want a single
    converter to cover a whole message package.
    """
    import dalaran as dl

    data = getattr(msg, "data", None)
    if isinstance(data, bool):
        ctx.log(entity_path, dl.Scalars(float(data)))
    elif isinstance(data, (int, float, np.integer, np.floating)):
        ctx.log(entity_path, dl.Scalars(float(data)))
    elif isinstance(data, (list, tuple, np.ndarray)):
        ctx.log(entity_path, dl.Scalars(np.asarray(data, dtype=np.float64).reshape(-1)))
    else:
        ctx.log(entity_path, dl.TextLog(str(data if data is not None else msg)))
