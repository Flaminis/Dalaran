from __future__ import annotations

import numpy as np
import pytest
from dalaran.robot import TransformTree
from dalaran.robot._math import euler_to_matrix, make_matrix


def _tree() -> TransformTree:
    tree = TransformTree(root="world")
    tree.add_chain("base_link", "arm", "gripper")
    return tree


def test_entity_paths_follow_the_frame_chain() -> None:
    tree = _tree()
    assert tree.entity_path("world") == "world"
    assert tree.entity_path("base_link") == "world/base_link"
    assert tree.entity_path("gripper") == "world/base_link/arm/gripper"
    assert tree.frames == ["world", "base_link", "arm", "gripper"]


def test_prefix_is_applied_to_the_root() -> None:
    tree = TransformTree(root="odom", prefix="robots/spot")
    tree.add("base_link")
    assert tree.entity_path("base_link") == "robots/spot/odom/base_link"


def test_duplicate_and_unknown_frames_are_rejected() -> None:
    tree = _tree()
    with pytest.raises(ValueError, match="already been declared"):
        tree.add("arm", parent="world")
    with pytest.raises(KeyError):
        tree.add("hand", parent="nonexistent")
    with pytest.raises(KeyError):
        tree.entity_path("nonexistent")


def test_root_from_composes_the_chain() -> None:
    tree = _tree()
    rng = np.random.default_rng(0)
    locals_ = {}
    for name in ("base_link", "arm", "gripper"):
        locals_[name] = tree.set(
            name,
            translation=rng.uniform(-2, 2, 3),
            rpy=rng.uniform(-3, 3, 3),
            log=False,
        )

    expected = locals_["base_link"] @ locals_["arm"] @ locals_["gripper"]
    np.testing.assert_allclose(tree.root_from("gripper"), expected, atol=1e-12)


def test_lookup_matches_tf2_semantics() -> None:
    tree = TransformTree()
    tree.set("base_link", parent="world", translation=[2.0, 0.0, 0.0], log=False)
    tree.set("lidar", parent="base_link", translation=[0.0, 0.0, 1.0], log=False)

    # The translation column of target_from_source is the source origin in target coordinates.
    np.testing.assert_allclose(tree.lookup("world", "lidar")[:3, 3], [2.0, 0.0, 1.0], atol=1e-12)
    np.testing.assert_allclose(tree.lookup("lidar", "world")[:3, 3], [-2.0, 0.0, -1.0], atol=1e-12)


def test_lookup_is_invertible_and_transitive() -> None:
    tree = _tree()
    rng = np.random.default_rng(7)
    for name in ("base_link", "arm", "gripper"):
        tree.set(name, translation=rng.uniform(-2, 2, 3), rpy=rng.uniform(-3, 3, 3), log=False)

    a_to_c = tree.lookup("base_link", "gripper")
    np.testing.assert_allclose(np.linalg.inv(a_to_c), tree.lookup("gripper", "base_link"), atol=1e-10)
    np.testing.assert_allclose(
        tree.lookup("base_link", "arm") @ tree.lookup("arm", "gripper"),
        a_to_c,
        atol=1e-12,
    )
    np.testing.assert_allclose(tree.lookup("arm", "arm"), np.eye(4), atol=1e-12)


def test_lookup_across_sibling_branches() -> None:
    tree = TransformTree()
    tree.set("base_link", parent="world", translation=[1.0, 0.0, 0.0], log=False)
    tree.set("lidar", parent="base_link", translation=[0.0, 0.0, 1.0], log=False)
    tree.set("camera", parent="base_link", translation=[0.5, 0.0, 0.0], log=False)

    # From the lidar, the camera is half a meter ahead and a meter down.
    np.testing.assert_allclose(tree.lookup("lidar", "camera")[:3, 3], [0.5, 0.0, -1.0], atol=1e-12)


def test_rotation_spellings_agree() -> None:
    rpy = [0.3, -0.2, 1.1]
    rotation = euler_to_matrix(rpy)
    quaternion = np.array([0.0, 0.0, 0.0, 1.0])

    expected = make_matrix(translation=[1.0, 2.0, 3.0], rotation=rotation)
    trees = []
    for kwargs in (
        {"rpy": rpy, "translation": [1.0, 2.0, 3.0]},
        {"rotation_matrix": rotation, "translation": [1.0, 2.0, 3.0]},
        {"matrix": expected},
    ):
        tree = TransformTree()
        trees.append(tree.set("base_link", parent="world", log=False, **kwargs))
    for actual in trees:
        np.testing.assert_allclose(actual, expected, atol=1e-12)

    tree = TransformTree()
    np.testing.assert_allclose(
        tree.set("base_link", parent="world", quaternion=quaternion, log=False),
        np.eye(4),
        atol=1e-12,
    )


def test_transform_points_between_frames() -> None:
    tree = TransformTree()
    tree.set("base_link", parent="world", translation=[1.0, 0.0, 0.0], rpy=[0.0, 0.0, np.pi / 2], log=False)

    # A point one meter ahead of the robot, which is facing +y.
    np.testing.assert_allclose(
        tree.transform_points([[1.0, 0.0, 0.0]], "base_link", "world"),
        [[1.0, 1.0, 0.0]],
        atol=1e-12,
    )


def test_setting_an_undeclared_frame_requires_a_parent() -> None:
    tree = TransformTree()
    with pytest.raises(KeyError, match="parent"):
        tree.set("lidar", translation=[0.0, 0.0, 0.0], log=False)
