from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pytest
from dalaran.robot import conventions
from dalaran.robot._math import euler_to_matrix, invert, make_matrix, matrix_to_quaternion, quaternion_to_matrix
from dalaran.robot.conventions import (
    FLU,
    RDF,
    Rep105Chain,
    enu_ned_matrix,
    enu_to_ned,
    enu_to_ned_quaternion,
    enu_to_ned_rotation_matrix,
    explain_convention,
    infer_convention,
    ned_to_enu,
    ned_to_enu_quaternion,
    ned_to_enu_rotation_matrix,
)


@pytest.fixture(autouse=True)
def _no_native_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    """`Rep105Chain` logs through the SDK, which this checkout may not have built."""

    class FakeArchetype:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    def fake_log(*_args: Any, **_kwargs: Any) -> None:
        return None

    dalaran = sys.modules["dalaran"]
    monkeypatch.setattr(dalaran, "log", fake_log, raising=False)
    monkeypatch.setattr(dalaran, "Transform3D", FakeArchetype, raising=False)


# -- ENU <-> NED, points ---------------------------------------------------


def test_enu_ned_matrix_is_an_involution_and_a_rotation() -> None:
    m = enu_ned_matrix()
    np.testing.assert_allclose(m @ m, np.eye(3), atol=1e-12)
    np.testing.assert_allclose(m @ m.T, np.eye(3), atol=1e-12)
    assert np.linalg.det(m) == pytest.approx(1.0)


def test_enu_to_ned_swaps_east_north_and_flips_up() -> None:
    np.testing.assert_allclose(enu_to_ned([3.0, 4.0, 5.0]), [4.0, 3.0, -5.0], atol=1e-12)
    np.testing.assert_allclose(ned_to_enu([4.0, 3.0, -5.0]), [3.0, 4.0, 5.0], atol=1e-12)


def test_point_round_trip_and_shape_preservation() -> None:
    rng = np.random.default_rng(7)
    points = rng.normal(size=(3, 4, 3))
    ned = enu_to_ned(points)
    assert ned.shape == points.shape
    np.testing.assert_allclose(ned_to_enu(ned), points, atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(ned, axis=-1), np.linalg.norm(points, axis=-1), atol=1e-12)


def test_a_bad_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="trailing dimension of 3"):
        enu_to_ned([[1.0, 2.0]])


# -- ENU <-> NED, orientations --------------------------------------------


def test_identity_in_enu_is_a_ninety_degree_heading_in_ned() -> None:
    """An FLU robot with identity orientation in ENU faces east, i.e. NED yaw = +90 degrees."""
    ned = enu_to_ned_rotation_matrix(np.eye(3))
    np.testing.assert_allclose(ned, euler_to_matrix([0.0, 0.0, np.pi / 2]), atol=1e-12)
    # Its FRD nose points north-east-down (0, 1, 0) = east.
    np.testing.assert_allclose(ned @ [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], atol=1e-12)


@pytest.mark.parametrize(
    ("yaw_enu", "yaw_ned"),
    [(0.0, np.pi / 2), (np.pi / 2, 0.0), (-np.pi / 2, np.pi), (0.3, np.pi / 2 - 0.3)],
)
def test_yaw_conversion_follows_the_ninety_minus_yaw_rule(yaw_enu: float, yaw_ned: float) -> None:
    ned = enu_to_ned_rotation_matrix(euler_to_matrix([0.0, 0.0, yaw_enu]))
    assert np.arctan2(ned[1, 0], ned[0, 0]) == pytest.approx(np.arctan2(np.sin(yaw_ned), np.cos(yaw_ned)))


def test_pitch_flips_sign_but_roll_does_not() -> None:
    """Nose-up is +pitch in FLU and -pitch in FRD, while a roll to the right is +roll in both."""
    from dalaran.robot._math import matrix_to_euler

    roll, pitch, yaw = matrix_to_euler(enu_to_ned_rotation_matrix(euler_to_matrix([0.2, -0.1, np.pi / 2])))
    assert roll == pytest.approx(0.2)
    assert pitch == pytest.approx(0.1)
    assert yaw == pytest.approx(0.0, abs=1e-12)


def test_rotation_round_trip() -> None:
    rng = np.random.default_rng(1)
    for _ in range(20):
        r = euler_to_matrix(rng.uniform(-np.pi, np.pi, size=3))
        np.testing.assert_allclose(ned_to_enu_rotation_matrix(enu_to_ned_rotation_matrix(r)), r, atol=1e-12)


def test_quaternion_round_trip_matches_the_matrix_path() -> None:
    rng = np.random.default_rng(2)
    for _ in range(20):
        q = matrix_to_quaternion(euler_to_matrix(rng.uniform(-np.pi, np.pi, size=3)))
        ned = enu_to_ned_quaternion(q)
        np.testing.assert_allclose(
            quaternion_to_matrix(ned),
            enu_to_ned_rotation_matrix(quaternion_to_matrix(q)),
            atol=1e-12,
        )
        np.testing.assert_allclose(
            quaternion_to_matrix(ned_to_enu_quaternion(ned)), quaternion_to_matrix(q), atol=1e-12
        )


def test_converted_orientations_stay_orthonormal() -> None:
    r = enu_to_ned_rotation_matrix(euler_to_matrix([0.3, 0.4, -1.1]))
    np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)
    assert np.linalg.det(r) == pytest.approx(1.0)


def test_a_bad_rotation_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="3x3 rotation matrix"):
        enu_to_ned_rotation_matrix(np.eye(4))


# -- ENU <-> NED, poses ----------------------------------------------------


def test_pose_conversion_moves_position_and_orientation_together() -> None:
    enu = make_matrix(translation=[10.0, 5.0, 2.0], rotation=euler_to_matrix([0.0, 0.0, np.pi / 2]))
    ned = enu_to_ned(enu)

    np.testing.assert_allclose(ned[:3, 3], [5.0, 10.0, -2.0], atol=1e-12)
    np.testing.assert_allclose(ned[:3, :3], enu_to_ned_rotation_matrix(enu[:3, :3]), atol=1e-12)
    np.testing.assert_allclose(ned_to_enu(ned), enu, atol=1e-12)


def test_pose_conversion_without_the_body_flip_is_a_pure_similarity() -> None:
    """A world-aligned child frame (a map tile, say) only needs its world axes re-expressed."""
    enu = make_matrix(translation=[1.0, 2.0, 3.0], rotation=euler_to_matrix([0.0, 0.0, 0.4]))
    ned = enu_to_ned(enu, body=False)
    world = make_matrix(rotation=enu_ned_matrix())
    np.testing.assert_allclose(ned, world @ enu @ invert(world), atol=1e-12)
    np.testing.assert_allclose(ned_to_enu(ned, body=False), enu, atol=1e-12)


def test_pose_conversion_preserves_relative_geometry() -> None:
    """Two converted poses keep their relative pose, expressed in the converted body axes."""
    a = make_matrix(translation=[1.0, 0.0, 0.0], rotation=euler_to_matrix([0.1, 0.2, 0.3]))
    b = make_matrix(translation=[4.0, -2.0, 1.0], rotation=euler_to_matrix([-0.4, 0.0, 1.2]))

    relative_enu = invert(a) @ b
    np.testing.assert_allclose(
        invert(enu_to_ned(a)) @ enu_to_ned(b),
        conventions.convert_frame_convention(relative_enu, FLU, conventions.FRD),
        atol=1e-12,
    )
    # Distances are geometry, so they survive either way.
    assert np.linalg.norm(enu_to_ned(a)[:3, 3] - enu_to_ned(b)[:3, 3]) == pytest.approx(
        np.linalg.norm(a[:3, 3] - b[:3, 3])
    )


# -- frame naming ----------------------------------------------------------


@pytest.mark.parametrize(
    "frame",
    ["camera_optical_frame", "camera_color_optical_frame", "left_camera_optical", "CAMERA_OPTICAL_FRAME"],
)
def test_optical_frame_names_imply_rdf(frame: str) -> None:
    assert infer_convention(frame) == RDF
    assert "optical" in explain_convention(frame).reason


@pytest.mark.parametrize("frame", ["base_link", "velodyne", "camera_link", "imu_link", "map", "odom"])
def test_everything_else_implies_flu(frame: str) -> None:
    assert infer_convention(frame) == FLU


def test_world_frames_get_their_own_explanation() -> None:
    assert "REP-105 world frame" in explain_convention("odom").reason
    assert "default applies" in explain_convention("velodyne").reason


def test_entity_path_style_names_are_understood() -> None:
    assert infer_convention("world/base_link/camera_optical_frame") == RDF
    assert explain_convention("/odom").convention == FLU


def test_explanation_carries_a_usable_matrix_and_string() -> None:
    optical = explain_convention("camera_optical_frame")
    assert optical.frame == "camera_optical_frame"
    np.testing.assert_allclose(
        optical.matrix_to(FLU),
        conventions.convention_matrix(RDF, FLU),
        atol=1e-12,
    )
    assert str(optical).startswith("camera_optical_frame: RDF (")


def test_the_inferred_convention_actually_rotates_a_camera_ray() -> None:
    """A ray pointing out of the lens is +Z in RDF and +X in FLU."""
    rot = explain_convention("camera_optical_frame").matrix_to(FLU)
    np.testing.assert_allclose(rot @ [0.0, 0.0, 1.0], [1.0, 0.0, 0.0], atol=1e-12)


# -- REP-105 chain ---------------------------------------------------------


def test_the_chain_is_declared_in_the_right_order() -> None:
    chain = Rep105Chain()
    assert chain.tree.path_to_root("base_link") == ["base_link", "odom", "map"]
    assert chain.tree.entity_path("base_link") == "map/odom/base_link"
    assert repr(chain) == "Rep105Chain(map='map', odom='odom', base='base_link')"


def test_localization_and_odometry_compose_into_the_map_pose() -> None:
    chain = Rep105Chain()
    chain.set_odometry(translation=[1.0, 0.0, 0.0], rpy=[0.0, 0.0, 0.1])
    chain.set_localization(translation=[0.05, -0.02, 0.0])

    np.testing.assert_allclose(chain.pose_in_map()[:3, 3], [1.05, -0.02, 0.0], atol=1e-9)
    np.testing.assert_allclose(chain.pose_in_odom()[:3, 3], [1.0, 0.0, 0.0], atol=1e-9)
    np.testing.assert_allclose(chain.localization_correction()[:3, 3], [0.05, -0.02, 0.0], atol=1e-9)


def test_localization_moves_odom_not_base() -> None:
    """The whole point of REP-105: a localization jump must not touch the odometry transform."""
    chain = Rep105Chain()
    chain.set_odometry(translation=[2.0, 0.0, 0.0])
    before = chain.pose_in_odom()
    chain.set_localization(translation=[100.0, 0.0, 0.0], rpy=[0.0, 0.0, 0.5])
    np.testing.assert_allclose(chain.pose_in_odom(), before, atol=1e-12)


def test_set_pose_in_map_derives_the_correction_instead_of_short_circuiting() -> None:
    chain = Rep105Chain()
    chain.set_odometry(translation=[10.0, 0.0, 0.0], rpy=[0.0, 0.0, 0.2])

    goal = make_matrix(translation=[10.5, 0.3, 0.0], rotation=euler_to_matrix([0.0, 0.0, 0.25]))
    correction = chain.set_pose_in_map(goal)

    np.testing.assert_allclose(chain.pose_in_map(), goal, atol=1e-9)
    # The odometry transform is untouched ...
    np.testing.assert_allclose(chain.pose_in_odom()[:3, 3], [10.0, 0.0, 0.0], atol=1e-12)
    # ... and the correction is exactly what was published on map -> odom.
    np.testing.assert_allclose(correction, chain.localization_correction(), atol=1e-12)
    np.testing.assert_allclose(correction, goal @ invert(chain.pose_in_odom()), atol=1e-12)


def test_set_pose_in_map_rejects_a_non_pose() -> None:
    with pytest.raises(ValueError, match=r"\(4, 4\) map_from_base"):
        Rep105Chain().set_pose_in_map(np.eye(3))


def test_a_chain_can_reuse_an_existing_tree() -> None:
    from dalaran.robot import TransformTree

    tree = TransformTree(root="map")
    tree.add("sensors", parent="map")
    chain = Rep105Chain(tree)
    assert chain.tree is tree
    assert "odom" in tree and "sensors" in tree


def test_a_tree_without_the_map_frame_is_refused() -> None:
    from dalaran.robot import TransformTree

    with pytest.raises(KeyError, match="pass a tree rooted at"):
        Rep105Chain(TransformTree(root="world"))


def test_custom_frame_names_are_honoured() -> None:
    from dalaran.robot import TransformTree

    chain = Rep105Chain(TransformTree(root="mars_map"), map_frame="mars_map", base_frame="rover_body")
    assert chain.tree.entity_path("rover_body") == "mars_map/odom/rover_body"


def test_attaching_a_sensor_reports_its_convention() -> None:
    chain = Rep105Chain()
    assert chain.attach("camera_color_optical_frame") == RDF
    assert chain.attach("velodyne") == FLU
    assert chain.tree.entity_path("velodyne") == "map/odom/base_link/velodyne"


def test_frame_name_constants_match_rep105() -> None:
    assert conventions.REP105_CHAIN == ("earth", "map", "odom", "base_link")
    assert conventions.BASE_FOOTPRINT_FRAME == "base_footprint"
    assert conventions.MAP_FRAME == "map"
