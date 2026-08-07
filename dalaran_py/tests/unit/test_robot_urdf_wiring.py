from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from dalaran.robot import Robot
from dalaran.robot.urdf_model import UrdfModel

if TYPE_CHECKING:
    from pathlib import Path

ARM_URDF = """
<robot name="arm">
  <link name="base_link"/>
  <link name="shoulder_link"/>
  <link name="gripper_link"/>
  <link name="left_finger_link"/>
  <link name="right_finger_link"/>
  <joint name="shoulder" type="revolute">
    <parent link="base_link"/>
    <child link="shoulder_link"/>
    <origin xyz="0 0 0.5"/>
    <axis xyz="0 0 1"/>
    <limit lower="-1.0" upper="1.0"/>
  </joint>
  <joint name="wrist_mount" type="fixed">
    <parent link="shoulder_link"/>
    <child link="gripper_link"/>
    <origin xyz="0.4 0 0"/>
  </joint>
  <joint name="left_finger" type="prismatic">
    <parent link="gripper_link"/>
    <child link="left_finger_link"/>
    <axis xyz="0 1 0"/>
    <limit lower="0.0" upper="0.04"/>
  </joint>
  <joint name="right_finger" type="prismatic">
    <parent link="gripper_link"/>
    <child link="right_finger_link"/>
    <axis xyz="0 1 0"/>
    <limit lower="-0.04" upper="0.0"/>
    <mimic joint="left_finger" multiplier="-1.0"/>
  </joint>
</robot>
"""


class FakeArchetype:
    """Stands in for the archetypes the SDK would build from the native bindings."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


@pytest.fixture(autouse=True)
def logged(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Any, bool]]:
    """
    Capture what the robot *would* log, without needing the native extension.

    `dalaran.robot` only imports `dalaran` lazily, from inside the logging
    functions, so replacing the three symbols it uses is enough.
    """
    calls: list[tuple[str, Any, bool]] = []

    def fake_log(entity_path: str, archetype: Any, *, static: bool = False, **_: Any) -> None:
        calls.append((entity_path, archetype, static))

    dalaran = sys.modules["dalaran"]
    monkeypatch.setattr(dalaran, "log", fake_log, raising=False)
    monkeypatch.setattr(dalaran, "Transform3D", FakeArchetype, raising=False)
    monkeypatch.setattr(dalaran, "Scalars", FakeArchetype, raising=False)
    return calls


def make_robot(**kwargs: Any) -> Robot:
    robot = Robot("arm")
    robot.load_urdf(UrdfModel.from_string(ARM_URDF), log_model=False, **kwargs)
    return robot


# -- loading ---------------------------------------------------------------


def test_urdf_links_become_frames() -> None:
    robot = make_robot()

    assert robot.urdf is not None
    assert robot.urdf.name == "arm"
    # The URDF root link is the same name as the base frame, so they are merged.
    assert robot.link_frame("base_link") == "base_link"
    assert robot.link_path("base_link") == "world/base_link"
    assert robot.link_path("left_finger_link") == "world/base_link/shoulder_link/gripper_link/left_finger_link"
    assert set(robot.tree.frames) >= {"base_link", "shoulder_link", "gripper_link", "left_finger_link"}


def test_loading_registers_the_moving_joints_only() -> None:
    robot = make_robot()
    assert sorted(robot.joints) == ["left_finger", "right_finger", "shoulder"]
    assert "wrist_mount" not in robot.joints


def test_fixed_joints_are_logged_statically(logged: list[Any]) -> None:
    make_robot()
    statics = {path for path, _, static in logged if static}
    assert "world/base_link/shoulder_link/gripper_link" in statics
    assert "world/base_link/shoulder_link" not in statics


def test_the_zero_pose_is_logged_on_load() -> None:
    robot = make_robot()
    np.testing.assert_allclose(robot.tree.lookup("base_link", "gripper_link")[:3, 3], [0.4, 0.0, 0.5])


def test_a_prefix_keeps_two_robots_apart() -> None:
    robot = Robot("left_arm", base_frame="left_base_link")
    robot.load_urdf(UrdfModel.from_string(ARM_URDF), prefix="left_", log_model=False)

    assert robot.link_frame("shoulder_link") == "left_shoulder_link"
    # The prefixed root link name equals the base frame, so the two are merged.
    assert robot.link_frame("base_link") == "left_base_link"
    assert robot.link_path("shoulder_link") == "world/left_base_link/left_shoulder_link"
    # Joint names are never prefixed: they must keep matching the messages.
    assert "shoulder" in robot.joints


def test_a_urdf_root_that_is_not_the_base_frame_hangs_off_it() -> None:
    robot = Robot("rover", base_frame="chassis")
    robot.load_urdf(UrdfModel.from_string(ARM_URDF), log_model=False)

    assert robot.link_frame("base_link") == "base_link"
    assert robot.link_path("base_link") == "world/chassis/base_link"
    # The URDF root is rigidly identical to the base frame ...
    np.testing.assert_allclose(robot.tree.lookup("chassis", "base_link"), np.eye(4), atol=1e-12)
    # ... so moving the base still moves the whole model.
    robot.log_pose(translation=[1.0, 0.0, 0.0])
    np.testing.assert_allclose(robot.tree.lookup("world", "shoulder_link")[:3, 3], [1.0, 0.0, 0.5])


def test_urdf_can_be_passed_to_the_constructor() -> None:
    robot = Robot("arm", urdf=UrdfModel.from_string(ARM_URDF))
    assert robot.urdf is not None
    assert "shoulder" in robot.joints


def test_urdf_can_be_loaded_from_a_file(tmp_path: Path) -> None:
    path = tmp_path / "arm.urdf"
    path.write_text(ARM_URDF, encoding="utf-8")
    robot = Robot("arm")
    robot.load_urdf(path, log_model=False)
    assert robot.urdf is not None and robot.urdf.name == "arm"


def test_loading_twice_is_refused() -> None:
    robot = make_robot()
    with pytest.raises(ValueError, match="already has a URDF loaded"):
        robot.load_urdf(UrdfModel.from_string(ARM_URDF), log_model=False)


def test_a_nonsense_source_is_refused() -> None:
    with pytest.raises(TypeError, match="Expected a URDF path"):
        Robot("arm", urdf=42)


def test_an_unknown_link_raises_a_helpful_error() -> None:
    robot = make_robot()
    with pytest.raises(KeyError, match="Unknown URDF link"):
        robot.link_frame("nope_link")


def test_missing_bindings_only_cost_the_geometry(tmp_path: Path) -> None:
    """Without the compiled extension the kinematics must still be wired up."""
    if "dalaran.urdf" in sys.modules:
        pytest.skip("the native bindings are available, so nothing warns")

    path = tmp_path / "arm.urdf"
    path.write_text(ARM_URDF, encoding="utf-8")
    robot = Robot("arm")
    with pytest.warns(UserWarning, match="geometry was not logged"):
        robot.load_urdf(path)
    assert "shoulder" in robot.joints


def test_a_urdf_tree_is_adopted_and_logged() -> None:
    """A native `UrdfTree` is duck-typed, so a stand-in exercises the same path."""
    model = UrdfModel.from_string(ARM_URDF)
    logged_models: list[Any] = []

    class FakeLink:
        name = "base_link"

    class FakeTree:
        name = "arm"

        def joints(self) -> list[Any]:
            return model.joints

        def root_link(self) -> FakeLink:
            return FakeLink()

        def log_urdf_to_recording(self, recording: Any = None) -> None:
            logged_models.append(recording)

    robot = Robot("arm", urdf=FakeTree())
    assert logged_models == [None]
    assert sorted(robot.joints) == ["left_finger", "right_finger", "shoulder"]


# -- animation -------------------------------------------------------------


def test_log_joint_states_moves_the_urdf_links() -> None:
    robot = make_robot()
    robot.log_joint_states(["shoulder"], [1.0])

    # A 1 rad shoulder rotation swings the 0.4 m link away from +X.
    world_from_gripper = robot.tree.lookup("world", "gripper_link")
    np.testing.assert_allclose(
        world_from_gripper[:3, 3],
        [0.4 * np.cos(1.0), 0.4 * np.sin(1.0), 0.5],
        atol=1e-12,
    )


def test_log_joint_states_clamps_to_the_urdf_limits() -> None:
    robot = make_robot()
    robot.log_joint_states(["shoulder"], [10.0])
    at_limit = np.array([0.4 * np.cos(1.0), 0.4 * np.sin(1.0), 0.5])
    np.testing.assert_allclose(robot.tree.lookup("world", "gripper_link")[:3, 3], at_limit, atol=1e-12)


def test_mimic_joints_move_without_being_mentioned() -> None:
    robot = make_robot()
    robot.log_joint_states(["left_finger"], [0.03])

    np.testing.assert_allclose(robot.tree.lookup("gripper_link", "left_finger_link")[:3, 3], [0.0, 0.03, 0.0])
    np.testing.assert_allclose(robot.tree.lookup("gripper_link", "right_finger_link")[:3, 3], [0.0, -0.03, 0.0])


def test_positions_are_still_plotted(logged: list[Any]) -> None:
    robot = make_robot()
    logged.clear()
    robot.log_joint_states(["shoulder"], [0.25], velocities=[1.5], efforts=[0.1])

    paths = [path for path, _, _ in logged]
    assert "world/arm/joints/shoulder/position" in paths
    assert "world/arm/joints/shoulder/velocity" in paths
    assert "world/arm/joints/shoulder/effort" in paths


def test_animate_false_only_plots() -> None:
    robot = make_robot()
    robot.log_joint_states(["shoulder"], [1.0], animate=False)

    zero_pose = robot.tree.lookup("base_link", "shoulder_link")
    np.testing.assert_allclose(zero_pose[:3, :3], np.eye(3), atol=1e-12)
    np.testing.assert_allclose(zero_pose[:3, 3], [0.0, 0.0, 0.5], atol=1e-12)


def test_unknown_joint_names_warn_once_and_do_not_crash(logged: list[Any]) -> None:
    robot = make_robot()
    with pytest.warns(UserWarning, match="not in the URDF"):
        robot.log_joint_states(["ghost", "shoulder"], [0.1, 0.2])

    # The value is still plotted ...
    assert "world/arm/joints/ghost/position" in [path for path, _, _ in logged]
    # ... and the second sighting is silent, so a 100 Hz loop stays readable.
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        robot.log_joint_states(["ghost"], [0.3])


def test_hand_declared_joints_still_work_alongside_a_urdf() -> None:
    robot = make_robot()
    robot.add_joint("pan", parent="base_link", frame="pan_frame", origin=[0.0, 0.0, 1.0])
    with pytest.warns(UserWarning, match="not in the URDF"):
        robot.log_joint_states(["unknown_joint"], [0.0])

    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        robot.log_joint_states(["pan"], [np.pi / 2])
    np.testing.assert_allclose(robot.tree.lookup("base_link", "pan_frame")[:3, 3], [0.0, 0.0, 1.0])


def test_repr_mentions_the_urdf() -> None:
    assert repr(make_robot()) == "Robot(name='arm', base_frame='base_link', joints=3, urdf='arm')"


def test_inline_urdf_markup_is_not_treated_as_a_path() -> None:
    """
    `Robot(urdf=...)` accepts URDF markup directly, not just a path.

    Passing a small inline URDF is common in tests and snippets. Before this was
    handled, the string was passed to `Path.read_text` and the OS raised a
    confusing "File name too long" error.
    """
    from dalaran.robot.robot import _looks_like_urdf_xml, _resolve_urdf_source

    markup = """<robot name="inline">
      <link name="base_link"/><link name="tip"/>
      <joint name="j" type="revolute">
        <parent link="base_link"/><child link="tip"/>
        <origin xyz="0 0 0.1"/><axis xyz="0 0 1"/>
        <limit lower="-1" upper="1" effort="1" velocity="1"/>
      </joint>
    </robot>"""

    assert _looks_like_urdf_xml(markup)
    assert _looks_like_urdf_xml("\n  <robot/>")
    assert not _looks_like_urdf_xml("/tmp/arm.urdf")
    assert not _looks_like_urdf_xml("arm.urdf")

    model, native = _resolve_urdf_source(markup)
    assert native is None
    assert model.actuated_joint_names == ["j"]
    assert model.root_link == "base_link"
