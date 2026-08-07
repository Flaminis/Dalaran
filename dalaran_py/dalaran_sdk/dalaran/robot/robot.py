"""The [`Robot`][dalaran.robot.Robot] handle, which owns a robot's frames, joints, pose and telemetry."""

from __future__ import annotations

import tempfile
import warnings
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt

from ._math import euler_to_matrix, make_matrix, quaternion_to_matrix
from .frames import TransformTree
from .urdf_model import UrdfModel

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from dalaran.recording_stream import RecordingStream

__all__ = ["Joint", "Robot"]

_DEFAULT_TRAJECTORY_COLOR = (255, 190, 60)


class Joint:
    """
    A revolute or prismatic joint declared on a [`Robot`][dalaran.robot.Robot].

    Declaring a joint links a joint *name* (the thing that appears in a
    `sensor_msgs/JointState` message) to a *frame* in the robot's transform tree,
    so that [`Robot.log_joint_states`][dalaran.robot.Robot.log_joint_states] can
    animate the tree instead of only drawing plots.
    """

    __slots__ = ("axis", "frame", "kind", "name", "origin")

    def __init__(
        self,
        name: str,
        *,
        frame: str,
        axis: npt.NDArray[np.float64],
        origin: npt.NDArray[np.float64],
        kind: str,
    ) -> None:
        self.name = name
        """The joint name, as used in joint-state messages."""

        self.frame = frame
        """The child frame this joint drives."""

        self.axis = axis
        """The unit joint axis, expressed in the parent frame."""

        self.origin = origin
        """The 4x4 `parent_from_child` transform at joint position zero."""

        self.kind = kind
        """Either `"revolute"` or `"prismatic"`."""

    def transform(self, position: float) -> npt.NDArray[np.float64]:
        """
        Return the `parent_from_child` transform for this joint at `position`.

        `position` is in radians for a revolute joint and in meters for a
        prismatic one.
        """
        if self.kind == "revolute":
            return self.origin @ make_matrix(rotation=_axis_angle_to_matrix(self.axis, position))
        return self.origin @ make_matrix(translation=self.axis * position)


def _axis_angle_to_matrix(axis: npt.NDArray[np.float64], angle: float) -> npt.NDArray[np.float64]:
    """Rodrigues' rotation formula for a unit `axis` and an `angle` in radians."""
    x, y, z = axis
    k = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=np.float64)
    return np.eye(3) + np.sin(angle) * k + (1.0 - np.cos(angle)) * (k @ k)


def _looks_like_urdf_xml(source: str) -> bool:
    """
    Detect URDF markup, as opposed to a path to a file containing it.

    Markup is recognized by its leading `<` after stripping whitespace.
    """
    return source.lstrip()[:1] == "<"


def _resolve_urdf_source(source: str | Path | UrdfModel | Any) -> tuple[UrdfModel, Any]:
    """
    Normalize whatever the caller passed into `(model, native_tree_or_None)`.

    A `str` may be either a path or the URDF markup itself; markup is detected by
    its leading `<`, because passing a small inline URDF is common in tests,
    snippets and generated robots, and treating it as a path fails with a
    confusing "File name too long" from the OS.

    A `dalaran.urdf.UrdfTree` is recognized by its duck-typed surface rather
    than by `isinstance`, so this keeps working without the native bindings.
    """
    if isinstance(source, UrdfModel):
        return source, None
    if isinstance(source, str) and _looks_like_urdf_xml(source):
        return UrdfModel.from_string(source), None
    if isinstance(source, (str, Path)):
        return UrdfModel.from_file(source), None
    if hasattr(source, "joints") and hasattr(source, "root_link"):
        return UrdfModel.from_urdf_tree(source), source
    msg = f"Expected a URDF path, a UrdfTree or a UrdfModel, got {type(source).__name__}"
    raise TypeError(msg)


class Robot:
    """
    A high-level handle for logging one robot.

    A `Robot` owns a [`TransformTree`][dalaran.robot.TransformTree] rooted at
    `root_frame` with `base_frame` attached to it, and derives all its entity
    paths from that tree. Everything that is not a frame - joint plots, twists,
    the driven trajectory - is logged under `<root_frame>/<name>`.

    All poses use the REP-103 convention: `x` forward, `y` left, `z` up, angles
    in radians, distances in meters.

    Parameters
    ----------
    name:
        A name for this robot, used for the non-frame entity paths and as the
        default timeline-independent label.
    base_frame:
        Name of the robot's body frame. When logging more than one robot into a
        recording, give each of them a distinct `base_frame` (or a distinct
        `prefix`) so their entity paths do not collide.
    root_frame:
        Name of the fixed world frame the robot is placed in.
    timeline:
        Name of the timeline used by [`Robot.timestep`][dalaran.robot.Robot.timestep].
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use. If left unspecified,
        defaults to the current active data recording, if there is one.
    prefix:
        Optional entity path prefix for this robot's frames.
    urdf:
        Optional robot description: a path to a URDF file, a
        [`dalaran.urdf.UrdfTree`][], or an already-parsed
        [`UrdfModel`][dalaran.robot.urdf_model.UrdfModel]. Shorthand for calling
        [`Robot.load_urdf`][dalaran.robot.Robot.load_urdf] right after
        construction.

    Examples
    --------
    ```python
    import numpy as np
    import dalaran as dl

    dl.init("dalaran_example_robot", spawn=True)

    robot = dl.robot.Robot("rover")
    robot.tree.add("lidar", parent="base_link")
    robot.tree.set("lidar", translation=[0.2, 0.0, 0.4], static=True)

    for step in range(100):
        with robot.timestep(step):
            t = step / 10.0
            robot.log_odometry(
                position=[t, np.sin(t), 0.0],
                rpy=[0.0, 0.0, np.cos(t)],
                linear_velocity=[1.0, 0.0, 0.0],
                angular_velocity=[0.0, 0.0, 0.3],
            )
    ```

    """

    def __init__(
        self,
        name: str,
        base_frame: str = "base_link",
        *,
        root_frame: str = "world",
        timeline: str = "time",
        recording: RecordingStream | None = None,
        prefix: str | None = None,
        urdf: str | Path | UrdfModel | Any | None = None,
    ) -> None:
        self.name = name
        """The robot's name."""

        self.timeline = timeline
        """The timeline used by [`Robot.timestep`][dalaran.robot.Robot.timestep]."""

        self._recording = recording
        self._base_frame = base_frame
        self._tree = TransformTree(root=root_frame, prefix=prefix, recording=recording)
        self._tree.add(base_frame, root_frame)
        self._joints: dict[str, Joint] = {}
        self._trajectory: list[list[float]] = []
        self._urdf: UrdfModel | None = None
        self._urdf_link_frames: dict[str, str] = {}
        self._urdf_joint_frames: dict[str, str] = {}
        self._unknown_joints_warned = False

        if urdf is not None:
            self.load_urdf(urdf)

    # -- structure ---------------------------------------------------------

    @property
    def tree(self) -> TransformTree:
        """The robot's [`TransformTree`][dalaran.robot.TransformTree]."""
        return self._tree

    @property
    def base_frame(self) -> str:
        """The name of the robot's body frame."""
        return self._base_frame

    @property
    def base_path(self) -> str:
        """The entity path of the robot's body frame, e.g. `"world/base_link"`."""
        return self._tree.entity_path(self._base_frame)

    @property
    def data_path(self) -> str:
        """The entity path non-frame telemetry is logged under, e.g. `"world/rover"`."""
        return f"{self._tree.entity_path(self._tree.root)}/{self.name}"

    @property
    def joints(self) -> list[str]:
        """The names of all declared joints, whether declared by hand or loaded from a URDF."""
        return list(self._joints) + [name for name in self._urdf_joint_frames if name not in self._joints]

    # -- URDF --------------------------------------------------------------

    @property
    def urdf(self) -> UrdfModel | None:
        """The loaded [`UrdfModel`][dalaran.robot.urdf_model.UrdfModel], or `None`."""
        return self._urdf

    def link_frame(self, link: str) -> str:
        """
        Return the transform-tree frame name that a URDF link was registered under.

        The names only differ from the URDF link names when `load_urdf` was
        given a `prefix`, or for the URDF root link when it was merged into the
        robot's base frame.
        """
        try:
            return self._urdf_link_frames[link]
        except KeyError:
            msg = f"Unknown URDF link {link!r}; this robot knows {sorted(self._urdf_link_frames)}"
            raise KeyError(msg) from None

    def link_path(self, link: str) -> str:
        """Return the entity path a URDF link's transform is logged to."""
        return self._tree.entity_path(self.link_frame(link))

    def load_urdf(
        self,
        source: str | Path | UrdfModel | Any,
        *,
        prefix: str | None = None,
        log_model: bool = True,
        entity_path_prefix: str | None = None,
    ) -> UrdfModel:
        """
        Load a robot description and wire its links and joints into this robot.

        This does three things at once:

        1. every URDF link becomes a frame in the robot's
           [`TransformTree`][dalaran.robot.TransformTree], hanging off the base
           frame, so `robot.tree.lookup("base_link", "gripper")` works;
        2. every joint's zero pose is logged, `fixed` joints as static data;
        3. every non-`fixed` joint is registered by name, so that
           [`Robot.log_joint_states`][dalaran.robot.Robot.log_joint_states]
           animates the real link tree - including `<mimic>` joints, which move
           even though they never appear in a `sensor_msgs/JointState` message.

        The URDF root link is *merged into* the robot's base frame when the two
        have the same name. When they differ, the root link is added as a child
        of the base frame with an identity transform, so `log_pose` keeps moving
        the whole robot and both names remain addressable.

        Parameters
        ----------
        source:
            A path to a URDF file, a [`dalaran.urdf.UrdfTree`][], or an
            already-parsed [`UrdfModel`][dalaran.robot.urdf_model.UrdfModel].
        prefix:
            Optional prefix for the frame names derived from the URDF links.
            Use it when loading the same URDF onto several robots in one
            recording. Joint *names* are never prefixed, because they have to
            keep matching the incoming joint-state messages.
        log_model:
            Whether to log the URDF's visual geometry. This needs the native
            bindings; when they are unavailable a warning is emitted and only
            the kinematics are set up.
        entity_path_prefix:
            Where the geometry is logged. Defaults to the base frame's entity
            path, so the model inherits the robot's pose.

        Returns
        -------
        UrdfModel
            The parsed model, also available afterwards as `robot.urdf`.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_robot_urdf", spawn=True)

        robot = dl.robot.Robot("arm", urdf="arm.urdf")
        for step in range(100):
            with robot.timestep(step):
                # No `add_joint` calls: the URDF already declared the joints.
                robot.log_joint_states(["shoulder", "elbow"], [np.sin(step / 10.0), 0.4])
        ```

        """
        if self._urdf is not None:
            msg = f"Robot {self.name!r} already has a URDF loaded"
            raise ValueError(msg)

        model, tree = _resolve_urdf_source(source)
        self._urdf = model

        if log_model:
            self._log_urdf_model(source, tree, entity_path_prefix=entity_path_prefix)

        self._register_urdf_frames(model, prefix=prefix)
        return model

    def _log_urdf_model(self, source: Any, tree: Any, *, entity_path_prefix: str | None) -> None:
        """Log the URDF's geometry, which is the one part that needs the native bindings."""
        target = self.base_path if entity_path_prefix is None else entity_path_prefix
        if tree is None:
            if isinstance(source, (str, Path)):
                try:
                    from dalaran.urdf import UrdfTree
                except ImportError:
                    warnings.warn(
                        "Could not import `dalaran.urdf`, so the URDF geometry was not logged; "
                        "the kinematics are still set up.",
                        UserWarning,
                        stacklevel=3,
                    )
                    return

                if isinstance(source, str) and _looks_like_urdf_xml(source):
                    # The native loader only takes a path, so inline markup has to be
                    # materialized. Relative mesh paths inside inline URDFs would
                    # resolve against the temporary directory, so they are unsupported
                    # here; a URDF with meshes should be passed as a path.
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir) / "inline.urdf"
                        tmp_path.write_text(source, encoding="utf-8")
                        tree = UrdfTree.from_file_path(str(tmp_path), target)
                        tree.log_urdf_to_recording(self._recording)
                    return

                tree = UrdfTree.from_file_path(source, target)
            else:
                # A pre-parsed `UrdfModel` carries no geometry to log.
                return
        tree.log_urdf_to_recording(self._recording)

    def _register_urdf_frames(self, model: UrdfModel, *, prefix: str | None) -> None:
        """Declare a frame per URDF link and log every joint's zero pose."""
        pre = prefix or ""
        root = model.root_link
        self._urdf_link_frames = {root: self._base_frame if pre + root == self._base_frame else pre + root}
        if self._urdf_link_frames[root] != self._base_frame:
            # A URDF whose root is called something else still has to hang off
            # the robot's body frame; the two are rigidly identical.
            self._tree.set(self._urdf_link_frames[root], parent=self._base_frame, static=True)

        for joint in model.iter_joints_parents_first():
            parent_frame = self._urdf_link_frames[joint.parent_link]
            child_frame = pre + joint.child_link
            self._urdf_link_frames[joint.child_link] = child_frame
            self._tree.set(
                child_frame,
                parent=parent_frame,
                matrix=joint.transform(0.0),
                static=not joint.is_moving,
            )
            if joint.is_moving:
                self._urdf_joint_frames[joint.name] = child_frame

    def _animate_urdf(self, positions: Mapping[str, float]) -> dict[str, npt.NDArray[np.float64]]:
        """Move every frame implied by `positions`, mimic joints included."""
        model = self._urdf
        if model is None:
            return {}
        moved: dict[str, npt.NDArray[np.float64]] = {}
        for name, value in model.resolve_positions(positions).items():
            frame = self._urdf_joint_frames.get(name)
            if frame is None:
                continue
            moved[frame] = self._tree.set(frame, matrix=model.joint(name).transform(value, clamp=False))
        return moved

    def _warn_unknown_joints(self, names: Sequence[str]) -> None:
        """Warn once about joint names this robot cannot place in its tree."""
        if self._urdf is None or self._unknown_joints_warned:
            return
        unknown = [name for name in self._urdf.unknown_joints(names) if name not in self._joints]
        if not unknown:
            return
        self._unknown_joints_warned = True
        warnings.warn(
            f"Joint(s) {sorted(set(unknown))} are not in the URDF loaded for robot {self.name!r}; "
            "their values are plotted but nothing moves. Further unknown joints are not reported.",
            UserWarning,
            stacklevel=3,
        )

    # -- time --------------------------------------------------------------

    @contextmanager
    def timestep(
        self,
        time: int | float | timedelta | datetime | np.datetime64 | np.timedelta64,
        *,
        timeline: str | None = None,
    ) -> Iterator[Robot]:
        """
        Set the timeline once for a whole block of logging.

        The kind of time is inferred from the argument: an `int` becomes a
        sequence index, a `float` or `timedelta` becomes a duration in seconds,
        and a `datetime` becomes an absolute timestamp.

        Parameters
        ----------
        time:
            The time to stamp everything logged inside the block with.
        timeline:
            Override the robot's default timeline for this block.

        Yields
        ------
        Robot
            The robot itself, so that `with robot.timestep(t) as r:` reads well.

        Examples
        --------
        ```python
        import dalaran as dl

        dl.init("dalaran_example_timestep", spawn=True)
        robot = dl.robot.Robot("rover")

        for step in range(10):
            with robot.timestep(step) as r:
                r.log_pose(translation=[float(step), 0.0, 0.0])
        ```

        """
        import dalaran as dl

        name = self.timeline if timeline is None else timeline
        if isinstance(time, bool):
            msg = "`time` must be a number, timedelta or datetime, not a bool"
            raise TypeError(msg)

        if isinstance(time, (int, np.integer)):
            dl.set_time(name, sequence=int(time), recording=self._recording)
        elif isinstance(time, (datetime, np.datetime64)):
            dl.set_time(name, timestamp=time, recording=self._recording)
        elif isinstance(time, (timedelta, np.timedelta64)):
            dl.set_time(name, duration=time, recording=self._recording)
        elif isinstance(time, (float, np.floating)):
            dl.set_time(name, duration=float(time), recording=self._recording)
        else:
            msg = f"Unsupported time type {type(time).__name__}"
            raise TypeError(msg)

        yield self

    # -- pose --------------------------------------------------------------

    def log_pose(
        self,
        *,
        translation: npt.ArrayLike | None = None,
        quaternion: npt.ArrayLike | None = None,
        rotation_matrix: npt.ArrayLike | None = None,
        rpy: npt.ArrayLike | None = None,
        matrix: npt.ArrayLike | None = None,
        frame: str | None = None,
        static: bool = False,
    ) -> npt.NDArray[np.float64]:
        """
        Log the pose of `frame` (the base frame by default) relative to its parent.

        The rotation may be given as a quaternion (`xyzw`), a 3x3 rotation
        matrix, fixed-axis `(roll, pitch, yaw)` angles, or a 4x4 homogeneous
        matrix; see [`TransformTree.set`][dalaran.robot.TransformTree.set].

        Parameters
        ----------
        translation:
            `(3,)` translation in the parent frame, in meters.
        quaternion:
            Rotation as `(x, y, z, w)`.
        rotation_matrix:
            Rotation as a `(3, 3)` matrix.
        rpy:
            Rotation as fixed-axis `(roll, pitch, yaw)` in radians.
        matrix:
            A `(4, 4)` homogeneous transform.
        frame:
            The frame to move. Defaults to the robot's base frame.
        static:
            Log as static data, for poses that never change.

        Returns
        -------
        numpy.ndarray
            The resulting `(4, 4)` `parent_from_child` transform.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_pose", spawn=True)
        robot = dl.robot.Robot("rover")
        robot.log_pose(translation=[1.0, 2.0, 0.0], rpy=[0.0, 0.0, np.pi / 4])
        ```

        """
        return self._tree.set(
            self._base_frame if frame is None else frame,
            translation=translation,
            quaternion=quaternion,
            rotation_matrix=rotation_matrix,
            rpy=rpy,
            matrix=matrix,
            static=static,
        )

    # -- joints ------------------------------------------------------------

    def add_joint(
        self,
        name: str,
        *,
        parent: str,
        frame: str | None = None,
        axis: npt.ArrayLike = (0.0, 0.0, 1.0),
        origin: npt.ArrayLike | None = None,
        rpy: npt.ArrayLike | None = None,
        kind: str = "revolute",
    ) -> Joint:
        """
        Declare a joint, linking a joint name to a frame in the transform tree.

        Once a joint is declared, [`Robot.log_joint_states`][dalaran.robot.Robot.log_joint_states]
        moves the corresponding frame as well as plotting the joint position.

        Parameters
        ----------
        name:
            The joint name, as it appears in joint-state messages.
        parent:
            The parent frame the joint is mounted on.
        frame:
            The child frame the joint drives. Defaults to `name`.
        axis:
            `(3,)` joint axis in the parent frame; normalized internally.
        origin:
            `(3,)` translation of the joint from its parent, in meters.
        rpy:
            `(3,)` fixed-axis rotation of the joint's zero position.
        kind:
            `"revolute"` (radians) or `"prismatic"` (meters).

        Returns
        -------
        Joint
            The declared joint.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_joints", spawn=True)
        robot = dl.robot.Robot("arm")
        robot.add_joint("shoulder", parent="base_link", origin=[0.0, 0.0, 0.2])
        robot.add_joint("elbow", parent="shoulder", origin=[0.0, 0.0, 0.4], axis=[0, 1, 0])
        robot.log_joint_states(["shoulder", "elbow"], [0.3, -0.6])
        ```

        """
        if kind not in ("revolute", "prismatic"):
            msg = f"`kind` must be 'revolute' or 'prismatic', got {kind!r}"
            raise ValueError(msg)
        if name in self._joints:
            msg = f"Joint {name!r} has already been declared"
            raise ValueError(msg)

        child = name if frame is None else frame
        if child not in self._tree:
            self._tree.add(child, parent)

        axis_arr = np.asarray(axis, dtype=np.float64).reshape(3)
        norm = float(np.linalg.norm(axis_arr))
        if norm < 1e-12:
            msg = f"Joint {name!r} has a zero-length axis"
            raise ValueError(msg)
        axis_arr = axis_arr / norm

        origin_matrix = make_matrix(
            translation=origin,
            rotation=None if rpy is None else euler_to_matrix(rpy),
        )
        joint = Joint(name, frame=child, axis=axis_arr, origin=origin_matrix, kind=kind)
        self._joints[name] = joint
        return joint

    def log_joint_states(
        self,
        names: Sequence[str],
        positions: npt.ArrayLike,
        *,
        velocities: npt.ArrayLike | None = None,
        efforts: npt.ArrayLike | None = None,
        animate: bool = True,
    ) -> None:
        """
        Log a `sensor_msgs/JointState`-style reading.

        Each joint position is logged as a scalar time series under
        `<data_path>/joints/<name>/position`, and joints that this robot knows
        about additionally move their frame in the transform tree. A joint is
        known if it was declared with
        [`Robot.add_joint`][dalaran.robot.Robot.add_joint] or if it came from a
        URDF loaded with [`Robot.load_urdf`][dalaran.robot.Robot.load_urdf]. With
        a URDF loaded, values are clamped into the joint limits and `<mimic>`
        joints follow their driver automatically.

        Once a URDF is loaded, joint names that it does not declare are still
        plotted, but the first time one shows up a `UserWarning` is emitted:
        a typo in a joint name is otherwise completely invisible.

        Parameters
        ----------
        names:
            The joint names, one per position.
        positions:
            `(N,)` joint positions: radians for revolute joints, meters for
            prismatic ones.
        velocities:
            Optional `(N,)` joint velocities.
        efforts:
            Optional `(N,)` joint efforts (torque or force).
        animate:
            Set to `False` to only plot the values without moving the tree.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_joint_states", spawn=True)
        robot = dl.robot.Robot("arm")
        robot.add_joint("shoulder", parent="base_link", origin=[0.0, 0.0, 0.2])

        for step in range(100):
            with robot.timestep(step):
                robot.log_joint_states(["shoulder"], [np.sin(step / 10.0)])
        ```

        """
        import dalaran as dl

        pos = np.asarray(positions, dtype=np.float64).reshape(-1)
        if len(names) != pos.shape[0]:
            msg = f"Got {len(names)} joint names but {pos.shape[0]} positions"
            raise ValueError(msg)

        extras: dict[str, npt.NDArray[np.float64] | None] = {
            "velocity": None if velocities is None else np.asarray(velocities, dtype=np.float64).reshape(-1),
            "effort": None if efforts is None else np.asarray(efforts, dtype=np.float64).reshape(-1),
        }
        for label, values in extras.items():
            if values is not None and values.shape[0] != pos.shape[0]:
                msg = f"Got {len(names)} joint names but {values.shape[0]} {label} values"
                raise ValueError(msg)

        for index, joint_name in enumerate(names):
            base = f"{self.data_path}/joints/{joint_name}"
            dl.log(f"{base}/position", dl.Scalars(float(pos[index])), recording=self._recording)
            for label, values in extras.items():
                if values is not None:
                    dl.log(f"{base}/{label}", dl.Scalars(float(values[index])), recording=self._recording)

            joint = self._joints.get(joint_name)
            if joint is not None and animate:
                self._tree.set(joint.frame, matrix=joint.transform(float(pos[index])))

        if animate and self._urdf is not None:
            self._animate_urdf({name: float(value) for name, value in zip(names, pos, strict=True)})
        self._warn_unknown_joints(names)

    # -- motion ------------------------------------------------------------

    def log_twist(
        self,
        *,
        linear: npt.ArrayLike | None = None,
        angular: npt.ArrayLike | None = None,
        entity_path: str | None = None,
        linear_scale: float = 1.0,
        angular_scale: float = 1.0,
        linear_color: tuple[int, int, int] = (80, 220, 120),
        angular_color: tuple[int, int, int] = (220, 120, 220),
    ) -> None:
        """
        Log a `geometry_msgs/Twist` as arrows in the robot's body frame.

        The arrows live on the base frame, so they follow the robot around; a
        linear velocity of `[1, 0, 0]` always points out of the robot's nose.

        Parameters
        ----------
        linear:
            `(3,)` linear velocity in m/s, in body coordinates.
        angular:
            `(3,)` angular velocity in rad/s, in body coordinates.
        entity_path:
            Override where the arrows are logged. Defaults to the base frame.
        linear_scale:
            Arrow length per m/s.
        angular_scale:
            Arrow length per rad/s.
        linear_color:
            RGB color of the linear velocity arrow.
        angular_color:
            RGB color of the angular velocity arrow.

        Examples
        --------
        ```python
        import dalaran as dl

        dl.init("dalaran_example_twist", spawn=True)
        robot = dl.robot.Robot("rover")
        robot.log_twist(linear=[1.0, 0.0, 0.0], angular=[0.0, 0.0, 0.5])
        ```

        """
        import dalaran as dl

        root = self.base_path if entity_path is None else entity_path
        for label, value, scale, color in (
            ("linear_velocity", linear, linear_scale, linear_color),
            ("angular_velocity", angular, angular_scale, angular_color),
        ):
            if value is None:
                continue
            vec = np.asarray(value, dtype=np.float64).reshape(3) * scale
            dl.log(
                f"{root}/{label}",
                dl.Arrows3D(vectors=[vec], origins=[[0.0, 0.0, 0.0]], colors=[color]),
                recording=self._recording,
            )

    def log_trajectory(
        self,
        points: npt.ArrayLike,
        *,
        entity_path: str | None = None,
        color: tuple[int, int, int] = _DEFAULT_TRAJECTORY_COLOR,
        radii: float = 0.02,
    ) -> None:
        """
        Log a path as a single 3D line strip, in root-frame coordinates.

        Parameters
        ----------
        points:
            `(N, 3)` points in the root frame.
        entity_path:
            Override where the strip is logged. Defaults to `<data_path>/trajectory`.
        color:
            RGB color of the line.
        radii:
            Line radius in meters.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_trajectory", spawn=True)
        robot = dl.robot.Robot("rover")

        t = np.linspace(0.0, 10.0, 200)
        robot.log_trajectory(np.stack([t, np.sin(t), np.zeros_like(t)], axis=1))
        ```

        """
        import dalaran as dl

        strip = np.asarray(points, dtype=np.float32)
        if strip.ndim != 2 or strip.shape[1] != 3:
            msg = f"`points` must have shape (N, 3), got {strip.shape}"
            raise ValueError(msg)

        path = f"{self.data_path}/trajectory" if entity_path is None else entity_path
        dl.log(path, dl.LineStrips3D([strip], colors=[color], radii=radii), recording=self._recording)

    def log_odometry(
        self,
        *,
        position: npt.ArrayLike,
        quaternion: npt.ArrayLike | None = None,
        rpy: npt.ArrayLike | None = None,
        rotation_matrix: npt.ArrayLike | None = None,
        linear_velocity: npt.ArrayLike | None = None,
        angular_velocity: npt.ArrayLike | None = None,
        trail: bool = True,
        max_trail: int = 10_000,
    ) -> npt.NDArray[np.float64]:
        """
        Log a `nav_msgs/Odometry`-style update: pose, twist and travelled path.

        This is the one call most teleop and navigation loops need. It moves the
        base frame, draws the body twist as arrows and extends the trajectory
        line with the new position.

        Parameters
        ----------
        position:
            `(3,)` position of the robot in the root frame, in meters.
        quaternion:
            Orientation as `(x, y, z, w)`.
        rpy:
            Orientation as fixed-axis `(roll, pitch, yaw)` in radians.
        rotation_matrix:
            Orientation as a `(3, 3)` matrix.
        linear_velocity:
            `(3,)` body-frame linear velocity in m/s.
        angular_velocity:
            `(3,)` body-frame angular velocity in rad/s.
        trail:
            Whether to accumulate and log the travelled path.
        max_trail:
            Maximum number of trail points kept in memory.

        Returns
        -------
        numpy.ndarray
            The resulting `(4, 4)` pose of the base frame.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_odometry", spawn=True)
        robot = dl.robot.Robot("rover")

        for step in range(200):
            t = step / 20.0
            with robot.timestep(t):
                robot.log_odometry(
                    position=[np.cos(t), np.sin(t), 0.0],
                    rpy=[0.0, 0.0, t + np.pi / 2],
                    linear_velocity=[1.0, 0.0, 0.0],
                    angular_velocity=[0.0, 0.0, 1.0],
                )
        ```

        """
        pose = self.log_pose(
            translation=position,
            quaternion=quaternion,
            rpy=rpy,
            rotation_matrix=rotation_matrix,
        )

        if linear_velocity is not None or angular_velocity is not None:
            self.log_twist(linear=linear_velocity, angular=angular_velocity)

        if trail:
            self._trajectory.append([float(v) for v in pose[:3, 3]])
            if len(self._trajectory) > max_trail:
                del self._trajectory[: len(self._trajectory) - max_trail]
            if len(self._trajectory) > 1:
                self.log_trajectory(np.asarray(self._trajectory, dtype=np.float32))

        return pose

    def clear_trajectory(self) -> None:
        """Forget the accumulated odometry trail without clearing what was already logged."""
        self._trajectory.clear()

    def log_orientation_quaternion(self, quaternion: npt.ArrayLike) -> npt.NDArray[np.float64]:
        """
        Log the base frame's orientation from a quaternion, keeping the current translation.

        Examples
        --------
        ```python
        import dalaran as dl

        dl.init("dalaran_example_orientation", spawn=True)
        robot = dl.robot.Robot("rover")
        robot.log_pose(translation=[1.0, 0.0, 0.0])
        robot.log_orientation_quaternion([0.0, 0.0, 0.0, 1.0])
        ```

        """
        current = self._tree.local(self._base_frame)
        return self.log_pose(
            translation=current[:3, 3],
            rotation_matrix=quaternion_to_matrix(quaternion),
        )

    def __repr__(self) -> str:
        urdf = "" if self._urdf is None else f", urdf={self._urdf.name!r}"
        return f"Robot(name={self.name!r}, base_frame={self._base_frame!r}, joints={len(self.joints)}{urdf})"
