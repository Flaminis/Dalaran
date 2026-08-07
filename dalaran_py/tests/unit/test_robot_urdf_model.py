from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pytest
from dalaran.robot._math import euler_to_matrix, invert
from dalaran.robot.urdf_model import (
    JointSpec,
    MimicSpec,
    UrdfModel,
    axis_angle_to_matrix,
)

if TYPE_CHECKING:
    from pathlib import Path

ARM_URDF = """
<robot name="arm">
  <link name="base_link"/>
  <link name="shoulder_link"/>
  <link name="elbow_link"/>
  <link name="tool_link"/>
  <joint name="shoulder" type="revolute">
    <parent link="base_link"/>
    <child link="shoulder_link"/>
    <origin xyz="0 0 0.2" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.2" upper="3.2" effort="30" velocity="2"/>
  </joint>
  <joint name="elbow" type="revolute">
    <parent link="shoulder_link"/>
    <child link="elbow_link"/>
    <origin xyz="0.4 0 0"/>
    <axis xyz="0 1 0"/>
    <limit lower="-2.0" upper="2.0"/>
  </joint>
  <joint name="tool" type="prismatic">
    <parent link="elbow_link"/>
    <child link="tool_link"/>
    <origin xyz="0.3 0 0"/>
    <axis xyz="1 0 0"/>
    <limit lower="0.0" upper="0.05"/>
  </joint>
</robot>
"""

GRIPPER_URDF = """
<robot name="gripper">
  <link name="palm"/>
  <link name="left_finger_link"/>
  <link name="right_finger_link"/>
  <link name="right_pad_link"/>
  <joint name="left_finger" type="prismatic">
    <parent link="palm"/>
    <child link="left_finger_link"/>
    <axis xyz="0 1 0"/>
    <limit lower="0.0" upper="0.04"/>
  </joint>
  <joint name="right_finger" type="prismatic">
    <parent link="palm"/>
    <child link="right_finger_link"/>
    <axis xyz="0 1 0"/>
    <limit lower="-0.04" upper="0.0"/>
    <mimic joint="left_finger" multiplier="-1.0"/>
  </joint>
  <joint name="right_pad" type="prismatic">
    <parent link="right_finger_link"/>
    <child link="right_pad_link"/>
    <axis xyz="0 1 0"/>
    <mimic joint="right_finger" multiplier="0.5" offset="0.01"/>
  </joint>
</robot>
"""


def test_parses_joint_metadata() -> None:
    model = UrdfModel.from_string(ARM_URDF)

    assert model.name == "arm"
    assert model.root_link == "base_link"
    assert model.joint_names == ["shoulder", "elbow", "tool"]
    assert model.actuated_joint_names == ["shoulder", "elbow", "tool"]
    assert model.mimic_joint_names == []

    shoulder = model.joint("shoulder")
    assert shoulder.joint_type == "revolute"
    assert shoulder.axis == (0.0, 0.0, 1.0)
    assert shoulder.origin_xyz == (0.0, 0.0, 0.2)
    assert (shoulder.limit_lower, shoulder.limit_upper) == (-3.2, 3.2)
    assert (shoulder.limit_effort, shoulder.limit_velocity) == (30.0, 2.0)
    assert shoulder.unit == "rad"
    assert model.joint("tool").unit == "m"
    assert "elbow" in model
    assert "wrist" not in model


def test_from_file(tmp_path: Path) -> None:
    path = tmp_path / "arm.urdf"
    path.write_text(ARM_URDF, encoding="utf-8")
    assert UrdfModel.from_file(path).joint_names == ["shoulder", "elbow", "tool"]


def test_unknown_joint_raises_with_a_helpful_message() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    with pytest.raises(KeyError, match="wrist"):
        model.joint("wrist")
    assert model.unknown_joints(["shoulder", "wrist", "elbow"]) == ["wrist"]


# -- limits ----------------------------------------------------------------


def test_limits_clamp_revolute_and_prismatic_joints() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    assert model.joint("shoulder").clamp(5.0) == 3.2
    assert model.joint("shoulder").clamp(-5.0) == -3.2
    assert model.joint("shoulder").clamp(0.25) == 0.25
    assert model.joint("tool").clamp(1.0) == 0.05


def test_continuous_joints_are_never_clamped() -> None:
    model = UrdfModel.from_string(
        '<robot name="wheel">'
        '<link name="base_link"/><link name="wheel_link"/>'
        '<joint name="wheel" type="continuous">'
        '<parent link="base_link"/><child link="wheel_link"/><axis xyz="0 1 0"/>'
        "</joint></robot>"
    )
    wheel = model.joint("wheel")
    assert wheel.limit_lower is None and wheel.limit_upper is None
    assert wheel.clamp(100.0) == 100.0
    # Ten full turns is physically the same pose as no turn at all.
    np.testing.assert_allclose(wheel.transform(20.0 * np.pi), np.eye(4), atol=1e-9)


def test_fixed_joints_ignore_their_value() -> None:
    model = UrdfModel.from_string(
        '<robot name="mount">'
        '<link name="base_link"/><link name="lidar_link"/>'
        '<joint name="lidar_mount" type="fixed">'
        '<parent link="base_link"/><child link="lidar_link"/>'
        '<origin xyz="0.1 0 0.3"/>'
        "</joint></robot>"
    )
    joint = model.joint("lidar_mount")
    assert not joint.is_moving
    assert not joint.is_actuated
    assert joint.unit == ""
    np.testing.assert_allclose(joint.transform(7.0), joint.origin_matrix())


def test_check_limits_reports_and_warns() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    with pytest.warns(UserWarning, match="shoulder=5"):
        violations = model.check_limits({"shoulder": 5.0, "elbow": 0.1, "nope": 99.0})
    assert violations == {"shoulder": 5.0}

    # `warn=False` still reports, but silently: this is the path a caller that
    # aggregates its own diagnostics takes.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert model.check_limits({"shoulder": 5.0}, warn=False) == {"shoulder": 5.0}


def test_resolve_positions_clamps_unless_disabled() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    assert model.resolve_positions({"shoulder": 5.0}) == {"shoulder": 3.2}
    assert model.resolve_positions({"shoulder": 5.0}, clamp=False) == {"shoulder": 5.0}
    # Unknown joints are dropped rather than raising; the caller reports them.
    assert model.resolve_positions({"nope": 1.0}) == {}


# -- mimic joints ----------------------------------------------------------


def test_mimic_chain_resolves_transitively() -> None:
    model = UrdfModel.from_string(GRIPPER_URDF)
    assert model.actuated_joint_names == ["left_finger"]
    assert model.mimic_joint_names == ["right_finger", "right_pad"]

    resolved = model.resolve_positions({"left_finger": 0.03})
    assert resolved["left_finger"] == pytest.approx(0.03)
    assert resolved["right_finger"] == pytest.approx(-0.03)
    # right_pad mimics right_finger, which itself mimics left_finger.
    assert resolved["right_pad"] == pytest.approx(0.5 * -0.03 + 0.01)


def test_mimic_result_is_clamped_by_the_mimic_joints_own_limits() -> None:
    model = UrdfModel.from_string(GRIPPER_URDF)
    # left_finger clamps to 0.04, so right_finger would be -0.04 exactly.
    resolved = model.resolve_positions({"left_finger": 10.0})
    assert resolved["left_finger"] == pytest.approx(0.04)
    assert resolved["right_finger"] == pytest.approx(-0.04)


def test_an_explicit_value_wins_over_the_mimic_relation() -> None:
    model = UrdfModel.from_string(GRIPPER_URDF)
    resolved = model.resolve_positions({"left_finger": 0.03, "right_finger": -0.01})
    assert resolved["right_finger"] == pytest.approx(-0.01)
    assert resolved["right_pad"] == pytest.approx(0.5 * -0.01 + 0.01)


def test_mimic_moves_the_link_tree() -> None:
    model = UrdfModel.from_string(GRIPPER_URDF)
    poses = model.link_transforms({"left_finger": 0.02})
    np.testing.assert_allclose(poses["left_finger_link"][:3, 3], [0.0, 0.02, 0.0], atol=1e-12)
    np.testing.assert_allclose(poses["right_finger_link"][:3, 3], [0.0, -0.02, 0.0], atol=1e-12)
    np.testing.assert_allclose(
        poses["right_pad_link"][:3, 3],
        [0.0, -0.02 + (0.5 * -0.02 + 0.01), 0.0],
        atol=1e-12,
    )


def test_mimicking_an_unknown_joint_is_rejected() -> None:
    with pytest.raises(ValueError, match="mimics unknown joint"):
        UrdfModel.from_string(
            '<robot name="bad">'
            '<link name="a"/><link name="b"/>'
            '<joint name="j" type="revolute"><parent link="a"/><child link="b"/>'
            '<mimic joint="ghost"/></joint></robot>'
        )


# -- forward kinematics ----------------------------------------------------


def test_forward_kinematics_through_revolute_and_prismatic_joints() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    poses = model.link_transforms({"shoulder": np.pi / 2, "elbow": 0.0, "tool": 0.05})

    np.testing.assert_allclose(poses["base_link"], np.eye(4), atol=1e-12)
    # The shoulder only rotates, so its link origin stays 0.2 m above the base.
    np.testing.assert_allclose(poses["shoulder_link"][:3, 3], [0.0, 0.0, 0.2], atol=1e-12)
    # A 90 degree yaw turns the 0.4 m upper arm from +X into +Y.
    np.testing.assert_allclose(poses["elbow_link"][:3, 3], [0.0, 0.4, 0.2], atol=1e-12)
    # 0.3 m of forearm plus 0.05 m of tool extension, still along the rotated +X.
    np.testing.assert_allclose(poses["tool_link"][:3, 3], [0.0, 0.75, 0.2], atol=1e-12)


def test_forward_kinematics_clamps_out_of_range_values() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    clamped = model.link_transforms({"tool": 10.0})
    at_limit = model.link_transforms({"tool": 0.05})
    np.testing.assert_allclose(clamped["tool_link"], at_limit["tool_link"], atol=1e-12)

    unclamped = model.link_transforms({"tool": 10.0}, clamp=False)
    assert unclamped["tool_link"][0, 3] == pytest.approx(0.7 + 10.0)


def test_missing_joints_are_held_at_zero() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    np.testing.assert_allclose(
        model.link_transforms({"shoulder": 0.3})["tool_link"],
        model.link_transforms({"shoulder": 0.3, "elbow": 0.0, "tool": 0.0})["tool_link"],
        atol=1e-12,
    )


def test_joint_origin_rotation_is_honoured() -> None:
    model = UrdfModel.from_string(
        '<robot name="tilted">'
        '<link name="base_link"/><link name="tilted_link"/>'
        '<joint name="tilt" type="prismatic">'
        '<parent link="base_link"/><child link="tilted_link"/>'
        '<origin xyz="1 0 0" rpy="0 0 1.5707963267948966"/>'
        '<axis xyz="1 0 0"/>'
        "</joint></robot>"
    )
    # The joint frame is yawed 90 degrees, so sliding along its +X moves along world +Y.
    poses = model.link_transforms({"tilt": 2.0})
    np.testing.assert_allclose(poses["tilted_link"][:3, 3], [1.0, 2.0, 0.0], atol=1e-12)
    np.testing.assert_allclose(poses["tilted_link"][:3, :3], euler_to_matrix([0, 0, np.pi / 2]), atol=1e-12)


def test_joint_transforms_are_local_and_composable() -> None:
    model = UrdfModel.from_string(ARM_URDF)
    positions = {"shoulder": 0.3, "elbow": -0.4, "tool": 0.01}
    local = model.joint_transforms(positions)
    poses = model.link_transforms(positions)
    np.testing.assert_allclose(
        poses["shoulder_link"] @ local["elbow"],
        poses["elbow_link"],
        atol=1e-12,
    )
    # And each local transform relates exactly the two links it connects.
    np.testing.assert_allclose(
        invert(poses["elbow_link"]) @ poses["tool_link"],
        local["tool"],
        atol=1e-12,
    )


def test_axis_is_normalized() -> None:
    model = UrdfModel.from_string(
        '<robot name="scaled">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j" type="prismatic"><parent link="a"/><child link="b"/>'
        '<axis xyz="0 0 5"/></joint></robot>'
    )
    np.testing.assert_allclose(model.joint("j").transform(2.0)[:3, 3], [0.0, 0.0, 2.0], atol=1e-12)


def test_zero_length_axis_is_rejected() -> None:
    joint = JointSpec("j", "revolute", "a", "b", axis=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="zero-length axis"):
        joint.transform(1.0)


def test_axis_angle_matches_euler_for_a_pure_yaw() -> None:
    np.testing.assert_allclose(
        axis_angle_to_matrix([0, 0, 1], 0.7),
        euler_to_matrix([0.0, 0.0, 0.7]),
        atol=1e-12,
    )


# -- ordering and structure ------------------------------------------------


def test_iter_joints_parents_first_handles_document_order_shuffles() -> None:
    model = UrdfModel.from_string(
        '<robot name="shuffled">'
        '<link name="base_link"/><link name="a"/><link name="b"/>'
        '<joint name="b_joint" type="fixed"><parent link="a"/><child link="b"/></joint>'
        '<joint name="a_joint" type="fixed"><parent link="base_link"/><child link="a"/></joint>'
        "</robot>"
    )
    assert [j.name for j in model.iter_joints_parents_first()] == ["a_joint", "b_joint"]
    seen: set[str] = {model.root_link}
    for joint in model.iter_joints_parents_first():
        assert joint.parent_link in seen
        seen.add(joint.child_link)


def test_links_referenced_only_by_joints_are_adopted() -> None:
    model = UrdfModel.from_string(
        '<robot name="sparse">'
        '<link name="base_link"/>'
        '<joint name="j" type="fixed"><parent link="base_link"/><child link="tip"/></joint>'
        "</robot>"
    )
    assert model.links == ["base_link", "tip"]
    assert model.root_link == "base_link"
    assert model.joint_for_child_link("tip").name == "j"
    assert model.joint_for_child_link("base_link") is None


# -- malformed URDFs -------------------------------------------------------


def test_non_robot_root_is_rejected() -> None:
    with pytest.raises(ValueError, match="Expected a <robot> root element"):
        UrdfModel.from_string("<sdf/>")


def test_joint_without_a_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="needs a `name` and a `type`"):
        UrdfModel.from_string('<robot name="x"><joint type="fixed"/></robot>')


def test_joint_without_parent_or_child_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing a <parent> or <child>"):
        UrdfModel.from_string('<robot name="x"><joint name="j" type="fixed"><parent link="a"/></joint></robot>')


def test_parent_without_a_link_attribute_is_rejected() -> None:
    with pytest.raises(ValueError, match="without a `link` attribute"):
        UrdfModel.from_string('<robot name="x"><joint name="j" type="fixed"><parent/><child link="b"/></joint></robot>')


def test_mimic_without_a_driver_is_rejected() -> None:
    with pytest.raises(ValueError, match="<mimic> tag without a `joint` attribute"):
        UrdfModel.from_string(
            '<robot name="x">'
            '<joint name="j" type="revolute"><parent link="a"/><child link="b"/><mimic/></joint>'
            "</robot>"
        )


def test_duplicate_joint_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate joint name"):
        UrdfModel.from_string(
            '<robot name="x">'
            '<joint name="j" type="fixed"><parent link="a"/><child link="b"/></joint>'
            '<joint name="j" type="fixed"><parent link="b"/><child link="c"/></joint>'
            "</robot>"
        )


def test_a_bad_origin_vector_is_rejected() -> None:
    with pytest.raises(ValueError, match="Expected 3 numbers"):
        UrdfModel.from_string(
            '<robot name="x">'
            '<joint name="j" type="fixed"><parent link="a"/><child link="b"/>'
            '<origin xyz="1 2"/></joint></robot>'
        )


def test_a_disconnected_model_has_no_single_root() -> None:
    model = UrdfModel.from_string(
        '<robot name="two">'
        '<joint name="j1" type="fixed"><parent link="a"/><child link="b"/></joint>'
        '<joint name="j2" type="fixed"><parent link="c"/><child link="d"/></joint>'
        "</robot>"
    )
    with pytest.raises(ValueError, match="disconnected"):
        _ = model.root_link


def test_a_cycle_has_no_root() -> None:
    model = UrdfModel.from_string(
        '<robot name="loop">'
        '<joint name="j1" type="fixed"><parent link="a"/><child link="b"/></joint>'
        '<joint name="j2" type="fixed"><parent link="b"/><child link="a"/></joint>'
        "</robot>"
    )
    with pytest.raises(ValueError, match="cycle"):
        _ = model.root_link


def test_a_cycle_below_the_root_is_reported_by_the_traversal() -> None:
    model = UrdfModel.from_string(
        '<robot name="loop">'
        '<link name="base_link"/>'
        '<joint name="j0" type="fixed"><parent link="base_link"/><child link="a"/></joint>'
        '<joint name="j1" type="fixed"><parent link="c"/><child link="b"/></joint>'
        '<joint name="j2" type="fixed"><parent link="b"/><child link="c"/></joint>'
        "</robot>"
    )
    with pytest.raises(ValueError, match="kinematic cycle"):
        list(model.iter_joints_parents_first())


# -- adopting a native UrdfTree -------------------------------------------


@dataclass
class FakeMimic:
    joint: str
    multiplier: float = 1.0
    offset: float = 0.0


@dataclass
class FakeJoint:
    name: str
    joint_type: str
    parent_link: str
    child_link: str
    axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    origin_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0)
    limit_lower: float | None = None
    limit_upper: float | None = None
    limit_effort: float | None = None
    limit_velocity: float | None = None
    mimic: FakeMimic | None = None


@dataclass
class FakeLink:
    name: str


class FakeTree:
    """A stand-in for the native `dalaran.urdf.UrdfTree`."""

    name = "fake"

    def __init__(self, joints: list[FakeJoint], root: str) -> None:
        self._joints = joints
        self._root = root

    def joints(self) -> list[FakeJoint]:
        return self._joints

    def root_link(self) -> FakeLink:
        return FakeLink(self._root)


def test_from_urdf_tree_adopts_the_duck_typed_surface() -> None:
    tree = FakeTree(
        [
            FakeJoint(
                "shoulder",
                "revolute",
                "base_link",
                "upper_arm",
                axis=(0.0, 0.0, 1.0),
                origin_xyz=(0.0, 0.0, 0.2),
                limit_lower=-1.0,
                limit_upper=1.0,
            ),
            FakeJoint(
                "mirror",
                "revolute",
                "base_link",
                "mirror_link",
                axis=(0.0, 0.0, 1.0),
                mimic=FakeMimic("shoulder", multiplier=-2.0, offset=0.1),
            ),
        ],
        root="base_link",
    )
    model = UrdfModel.from_urdf_tree(tree)

    assert model.name == "fake"
    assert model.root_link == "base_link"
    assert model.actuated_joint_names == ["shoulder"]
    assert model.joint("shoulder").limit_upper == 1.0
    resolved = model.resolve_positions({"shoulder": 0.5})
    assert resolved["mirror"] == pytest.approx(-2.0 * 0.5 + 0.1)
    np.testing.assert_allclose(model.link_transforms(resolved)["upper_arm"][:3, 3], [0, 0, 0.2])


def test_from_urdf_tree_maps_infinite_limits_to_none() -> None:
    tree = FakeTree(
        [FakeJoint("wheel", "continuous", "base_link", "wheel_link", limit_lower=-np.inf, limit_upper=np.inf)],
        root="base_link",
    )
    joint = UrdfModel.from_urdf_tree(tree).joint("wheel")
    assert joint.limit_lower is None
    assert joint.limit_upper is None
    assert joint.clamp(1000.0) == 1000.0


def test_mimic_spec_apply() -> None:
    assert MimicSpec("driver", multiplier=-1.0, offset=0.25).apply(0.5) == pytest.approx(-0.25)


def test_repr_is_informative() -> None:
    assert repr(UrdfModel.from_string(ARM_URDF)) == "UrdfModel(name='arm', links=4, joints=3)"
