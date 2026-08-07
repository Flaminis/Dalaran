from __future__ import annotations

import numpy as np
import pytest
from dalaran.robot import laser_scan_to_points
from dalaran.robot._math import euler_to_matrix, make_matrix
from dalaran.robot.robot import Joint, _axis_angle_to_matrix


def test_laser_scan_projection_is_rep103() -> None:
    points = laser_scan_to_points([1.0, 2.0, 3.0, 4.0], angle_min=0.0, angle_increment=np.pi / 2)
    # Angle zero is straight ahead (+x) and angles grow towards the left (+y).
    np.testing.assert_allclose(points[0], [1.0, 0.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(points[1], [0.0, 2.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(points[2], [-3.0, 0.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(points[3], [0.0, -4.0, 0.0], atol=1e-6)


def test_laser_scan_drops_invalid_beams() -> None:
    points = laser_scan_to_points(
        [1.0, np.inf, 2.0, np.nan, -np.inf],
        angle_min=0.0,
        angle_increment=0.1,
    )
    assert points.shape == (2, 3)
    np.testing.assert_allclose(np.linalg.norm(points, axis=1), [1.0, 2.0], atol=1e-6)


def test_laser_scan_respects_range_limits() -> None:
    points = laser_scan_to_points(
        [0.05, 5.0, 100.0],
        angle_min=0.0,
        angle_increment=0.1,
        range_min=0.1,
        range_max=50.0,
    )
    assert points.shape == (1, 3)
    assert np.linalg.norm(points) == pytest.approx(5.0, abs=1e-5)


def test_laser_scan_angle_max_matches_angle_increment() -> None:
    ranges = np.linspace(1.0, 2.0, 7)
    by_increment = laser_scan_to_points(ranges, angle_min=-np.pi / 2, angle_increment=np.pi / 6)
    by_max = laser_scan_to_points(ranges, angle_min=-np.pi / 2, angle_max=np.pi / 2)
    np.testing.assert_allclose(by_increment, by_max, atol=1e-6)


def test_laser_scan_keeps_the_scan_plane_height() -> None:
    points = laser_scan_to_points([1.0, 1.0], angle_min=0.0, angle_increment=0.1, z=0.25)
    np.testing.assert_allclose(points[:, 2], [0.25, 0.25], atol=1e-6)


def test_laser_scan_requires_exactly_one_angle_spec() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        laser_scan_to_points([1.0], angle_min=0.0)
    with pytest.raises(ValueError, match="exactly one"):
        laser_scan_to_points([1.0], angle_min=0.0, angle_increment=0.1, angle_max=1.0)


def test_laser_scan_of_an_empty_scan() -> None:
    assert laser_scan_to_points([], angle_min=0.0, angle_increment=0.1).shape == (0, 3)


@pytest.mark.parametrize("angle", [-2.5, -0.3, 0.0, 0.7, 3.0])
def test_axis_angle_matches_euler_about_z(angle: float) -> None:
    np.testing.assert_allclose(
        _axis_angle_to_matrix(np.array([0.0, 0.0, 1.0]), angle),
        euler_to_matrix([0.0, 0.0, angle]),
        atol=1e-12,
    )


def test_axis_angle_leaves_its_axis_fixed() -> None:
    rng = np.random.default_rng(0)
    for _ in range(100):
        axis = rng.normal(size=3)
        axis /= np.linalg.norm(axis)
        r = _axis_angle_to_matrix(axis, rng.uniform(-np.pi, np.pi))
        np.testing.assert_allclose(r @ axis, axis, atol=1e-12)
        np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)


def test_revolute_joint_transform() -> None:
    joint = Joint(
        "elbow",
        frame="elbow",
        axis=np.array([0.0, 1.0, 0.0]),
        origin=make_matrix(translation=[0.0, 0.0, 0.4]),
        kind="revolute",
    )
    np.testing.assert_allclose(joint.transform(0.0), make_matrix(translation=[0.0, 0.0, 0.4]), atol=1e-12)
    # A quarter turn about +y takes the link's +z into +x.
    np.testing.assert_allclose(joint.transform(np.pi / 2)[:3, :3] @ [0, 0, 1], [1, 0, 0], atol=1e-12)


def test_prismatic_joint_transform() -> None:
    joint = Joint(
        "slide",
        frame="slide",
        axis=np.array([1.0, 0.0, 0.0]),
        origin=make_matrix(translation=[0.0, 0.0, 1.0]),
        kind="prismatic",
    )
    np.testing.assert_allclose(joint.transform(0.5)[:3, 3], [0.5, 0.0, 1.0], atol=1e-12)
