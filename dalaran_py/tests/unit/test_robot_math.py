from __future__ import annotations

import numpy as np
import pytest
from dalaran.robot._math import (
    compose,
    euler_to_matrix,
    identity,
    invert,
    make_matrix,
    matrix_to_euler,
    matrix_to_quaternion,
    quaternion_to_matrix,
    resolve_rotation,
    transform_points,
)


def _random_rotations(count: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rpy = rng.uniform(-np.pi, np.pi, size=(count, 3))
    # Stay away from gimbal lock, which is tested separately.
    rpy[:, 1] = rng.uniform(-np.pi / 2 + 0.05, np.pi / 2 - 0.05, size=count)
    return rpy


def test_euler_matrix_is_orthonormal_and_right_handed() -> None:
    for rpy in _random_rotations(200):
        r = euler_to_matrix(rpy)
        np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)
        assert np.linalg.det(r) == pytest.approx(1.0)


def test_euler_follows_rep103() -> None:
    # Yaw turns "forward" (+x) into "left" (+y).
    np.testing.assert_allclose(euler_to_matrix([0.0, 0.0, np.pi / 2]) @ [1, 0, 0], [0, 1, 0], atol=1e-12)
    # Pitch tips "forward" (+x) down (-z).
    np.testing.assert_allclose(euler_to_matrix([0.0, np.pi / 2, 0.0]) @ [1, 0, 0], [0, 0, -1], atol=1e-12)
    # Roll turns "left" (+y) into "up" (+z).
    np.testing.assert_allclose(euler_to_matrix([np.pi / 2, 0.0, 0.0]) @ [0, 1, 0], [0, 0, 1], atol=1e-12)


def test_euler_round_trip() -> None:
    for rpy in _random_rotations(500, seed=1):
        np.testing.assert_allclose(matrix_to_euler(euler_to_matrix(rpy)), rpy, atol=1e-9)


@pytest.mark.parametrize("pitch", [np.pi / 2, -np.pi / 2])
@pytest.mark.parametrize("yaw", [-2.0, 0.0, 0.7, 3.0])
def test_euler_round_trip_at_gimbal_lock(pitch: float, yaw: float) -> None:
    # Roll and yaw are degenerate here, so only the resulting rotation can round-trip.
    r = euler_to_matrix([0.0, pitch, yaw])
    np.testing.assert_allclose(euler_to_matrix(matrix_to_euler(r)), r, atol=1e-9)


def test_quaternion_round_trip() -> None:
    for rpy in _random_rotations(500, seed=2):
        r = euler_to_matrix(rpy)
        np.testing.assert_allclose(quaternion_to_matrix(matrix_to_quaternion(r)), r, atol=1e-9)


@pytest.mark.parametrize("axis", [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
def test_quaternion_round_trip_at_180_degrees(axis: list[float]) -> None:
    # The trace-based branch is singular here; this is where naive implementations break.
    q = np.array([*axis, 0.0], dtype=np.float64)
    r = quaternion_to_matrix(q)
    np.testing.assert_allclose(quaternion_to_matrix(matrix_to_quaternion(r)), r, atol=1e-9)


def test_quaternion_is_normalized() -> None:
    r = quaternion_to_matrix([0.0, 0.0, 3.0, 3.0])
    np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)


def test_zero_quaternion_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero-length"):
        quaternion_to_matrix([0.0, 0.0, 0.0, 0.0])


def test_invert_is_exact_for_rigid_transforms() -> None:
    rng = np.random.default_rng(3)
    for rpy in _random_rotations(200, seed=4):
        t = make_matrix(translation=rng.uniform(-5, 5, 3), rotation=euler_to_matrix(rpy))
        np.testing.assert_allclose(compose(invert(t), t), identity(), atol=1e-12)
        np.testing.assert_allclose(invert(t), np.linalg.inv(t), atol=1e-10)


def test_compose_is_left_to_right() -> None:
    a = make_matrix(translation=[1, 0, 0], rotation=euler_to_matrix([0, 0, np.pi / 2]))
    b = make_matrix(translation=[1, 0, 0])
    # Applying `a` after `b` moves one meter along `a`'s rotated x axis.
    np.testing.assert_allclose(compose(a, b)[:3, 3], [1, 1, 0], atol=1e-12)
    np.testing.assert_allclose(compose(a, b), a @ b, atol=1e-12)


def test_transform_points() -> None:
    t = make_matrix(translation=[0, 0, 1], rotation=euler_to_matrix([0, 0, np.pi / 2]))
    np.testing.assert_allclose(transform_points(t, [[1.0, 0.0, 0.0]]), [[0.0, 1.0, 1.0]], atol=1e-12)
    np.testing.assert_allclose(transform_points(t, [1.0, 0.0, 0.0]), [0.0, 1.0, 1.0], atol=1e-12)


def test_resolve_rotation_accepts_one_spelling() -> None:
    expected = euler_to_matrix([0.1, 0.2, 0.3])
    quat = matrix_to_quaternion(expected)

    for kwargs in (
        {"rpy": [0.1, 0.2, 0.3]},
        {"quaternion": quat},
        {"rotation_matrix": expected},
        {"matrix": make_matrix(translation=[1, 2, 3], rotation=expected)},
    ):
        rotation, _ = resolve_rotation(**kwargs)  # type: ignore[arg-type]
        assert rotation is not None
        np.testing.assert_allclose(rotation, expected, atol=1e-9)

    _, translation = resolve_rotation(matrix=make_matrix(translation=[1, 2, 3], rotation=expected))
    np.testing.assert_allclose(translation, [1, 2, 3])


def test_resolve_rotation_rejects_ambiguity() -> None:
    with pytest.raises(ValueError, match="at most one rotation argument"):
        resolve_rotation(rpy=[0, 0, 0], quaternion=[0, 0, 0, 1])


def test_shape_errors() -> None:
    with pytest.raises(ValueError, match="4x4"):
        invert(np.eye(3))
    with pytest.raises(ValueError, match="3x3"):
        make_matrix(rotation=np.eye(4))
