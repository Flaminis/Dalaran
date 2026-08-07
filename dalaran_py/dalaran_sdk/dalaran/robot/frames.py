"""
A named coordinate-frame tree that logs [`dalaran.Transform3D`][] for you.

This is the piece that turns "I have a `tf` tree" into "I have a Dalaran entity
hierarchy", without you having to remember which entity path a given transform
belongs on, or which direction a transform points.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._math import (
    compose,
    identity,
    invert,
    make_matrix,
    matrix_to_quaternion,
    resolve_rotation,
)

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    from dalaran.recording_stream import RecordingStream

__all__ = ["Frame", "TransformTree"]


class Frame:
    """
    A single named coordinate frame inside a [`TransformTree`][dalaran.robot.TransformTree].

    You normally never construct this yourself; use
    [`TransformTree.add`][dalaran.robot.TransformTree.add] instead.
    """

    __slots__ = ("entity_path", "local", "name", "parent")

    def __init__(self, name: str, parent: str | None, entity_path: str) -> None:
        self.name = name
        """The frame's unique name, e.g. `"base_link"`."""

        self.parent = parent
        """The name of the parent frame, or `None` for the root."""

        self.entity_path = entity_path
        """The Dalaran entity path this frame's transform is logged to."""

        self.local: npt.NDArray[np.float64] = identity()
        """The most recent `parent_from_child` transform, as a 4x4 matrix."""

    def __repr__(self) -> str:
        return f"Frame(name={self.name!r}, parent={self.parent!r}, entity_path={self.entity_path!r})"


class TransformTree:
    """
    Declare named frames once, then log transforms by name.

    Every frame maps to an entity path built from the chain of frame names, so
    declaring `world -> base_link -> lidar` gives you the entity path
    `world/base_link/lidar`. Logging a transform for `lidar` then automatically
    lands on the right entity, and the viewer composes the chain for you.

    Transforms follow the Dalaran (and ROS) convention: the transform stored for
    a frame is `parent_from_child`, i.e. it maps points expressed in the child
    frame into the parent frame.

    Parameters
    ----------
    root:
        Name of the root frame. Defaults to `"world"`.
    prefix:
        Optional entity path prefix, e.g. `"robots/spot"`. Useful when logging
        several robots into the same recording.
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use. If left unspecified,
        defaults to the current active data recording, if there is one.

    Examples
    --------
    ```python
    import numpy as np
    import dalaran as dl

    dl.init("dalaran_example_transform_tree", spawn=True)

    tree = dl.robot.TransformTree(root="world")
    tree.add("base_link", parent="world")
    tree.add("lidar", parent="base_link")

    tree.set("base_link", translation=[1.0, 0.0, 0.0], rpy=[0.0, 0.0, np.pi / 2])
    tree.set("lidar", translation=[0.0, 0.0, 0.3])

    # Where is the lidar in world coordinates?
    world_from_lidar = tree.lookup("world", "lidar")
    print(world_from_lidar[:3, 3])  # [1. 0. 0.3]
    ```

    """

    def __init__(
        self,
        root: str = "world",
        *,
        prefix: str | None = None,
        recording: RecordingStream | None = None,
    ) -> None:
        self._prefix = prefix.strip("/") if prefix else None
        self._recording = recording
        self._frames: dict[str, Frame] = {}
        self._root = root
        self._frames[root] = Frame(root, None, self._make_entity_path(root, None))

    # -- structure ---------------------------------------------------------

    @property
    def root(self) -> str:
        """The name of the root frame."""
        return self._root

    @property
    def frames(self) -> list[str]:
        """The names of all declared frames, parents before children."""
        return list(self._frames)

    def __contains__(self, frame: str) -> bool:
        return frame in self._frames

    def _make_entity_path(self, name: str, parent: str | None) -> str:
        if parent is None:
            return f"{self._prefix}/{name}" if self._prefix else name
        return f"{self._frames[parent].entity_path}/{name}"

    def add(self, name: str, parent: str | None = None) -> Frame:
        """
        Declare a frame and attach it to `parent`.

        Parameters
        ----------
        name:
            The new frame's name. Must be unique within the tree.
        parent:
            The parent frame's name. Defaults to the tree's root frame.

        Returns
        -------
        Frame
            The newly declared frame.

        Examples
        --------
        ```python
        import dalaran as dl

        tree = dl.robot.TransformTree()
        tree.add("base_link")  # parented to "world"
        tree.add("camera", parent="base_link")
        assert tree.entity_path("camera") == "world/base_link/camera"
        ```

        """
        if name in self._frames:
            msg = f"Frame {name!r} has already been declared"
            raise ValueError(msg)
        parent_name = self._root if parent is None else parent
        if parent_name not in self._frames:
            msg = f"Unknown parent frame {parent_name!r}; declare it before its children"
            raise KeyError(msg)
        frame = Frame(name, parent_name, self._make_entity_path(name, parent_name))
        self._frames[name] = frame
        return frame

    def add_chain(self, *names: str, parent: str | None = None) -> None:
        """
        Declare a chain of frames, each parented to the previous one.

        Examples
        --------
        ```python
        import dalaran as dl

        tree = dl.robot.TransformTree()
        tree.add_chain("base_link", "arm", "gripper")
        assert tree.entity_path("gripper") == "world/base_link/arm/gripper"
        ```

        """
        current = parent
        for name in names:
            self.add(name, current)
            current = name

    def frame(self, name: str) -> Frame:
        """Return the [`Frame`][dalaran.robot.Frame] called `name`, raising `KeyError` if unknown."""
        try:
            return self._frames[name]
        except KeyError:
            msg = f"Unknown frame {name!r}; known frames are {sorted(self._frames)}"
            raise KeyError(msg) from None

    def entity_path(self, name: str) -> str:
        """Return the Dalaran entity path that frame `name` is logged to."""
        return self.frame(name).entity_path

    # -- transforms --------------------------------------------------------

    def set(
        self,
        frame: str,
        *,
        translation: npt.ArrayLike | None = None,
        quaternion: npt.ArrayLike | None = None,
        rotation_matrix: npt.ArrayLike | None = None,
        rpy: npt.ArrayLike | None = None,
        matrix: npt.ArrayLike | None = None,
        parent: str | None = None,
        log: bool = True,
        static: bool = False,
    ) -> npt.NDArray[np.float64]:
        """
        Set (and by default log) the `parent_from_child` transform of `frame`.

        The rotation may be given in whichever form your data already has: a
        quaternion in `xyzw` order, a 3x3 rotation matrix, fixed-axis
        `(roll, pitch, yaw)` angles in radians, or a full 4x4 homogeneous matrix.
        At most one of them may be given.

        Parameters
        ----------
        frame:
            The frame to update. If it has not been declared yet, `parent` must
            be given and the frame is declared on the fly.
        translation:
            `(3,)` translation of the child frame's origin in parent coordinates.
        quaternion:
            Rotation as `(x, y, z, w)`.
        rotation_matrix:
            Rotation as a `(3, 3)` matrix.
        rpy:
            Rotation as fixed-axis `(roll, pitch, yaw)` in radians (REP-103 / URDF).
        matrix:
            A `(4, 4)` homogeneous transform. Supplies both rotation and
            translation; combining it with `translation` overrides the
            translation part.
        parent:
            Parent frame, used only when `frame` is being declared on the fly.
        log:
            Set to `False` to update the tree without emitting a log message.
        static:
            Log the transform as static data. Use this for transforms that never
            change, such as a rigidly bolted-on sensor.

        Returns
        -------
        numpy.ndarray
            The resulting `(4, 4)` `parent_from_child` transform.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        dl.init("dalaran_example_tree_set", spawn=True)

        tree = dl.robot.TransformTree()
        tree.set("base_link", parent="world", translation=[0.0, 0.0, 0.1])
        tree.set("lidar", parent="base_link", translation=[0.2, 0.0, 0.3], static=True)
        tree.set("base_link", rpy=[0.0, 0.0, np.deg2rad(45.0)], translation=[1.0, 0.0, 0.1])
        ```

        """
        if frame not in self._frames:
            if parent is None and frame != self._root:
                msg = f"Unknown frame {frame!r}; pass `parent=` to declare it on the fly"
                raise KeyError(msg)
            self.add(frame, parent)

        rotation, matrix_translation = resolve_rotation(
            quaternion=quaternion,
            rotation_matrix=rotation_matrix,
            rpy=rpy,
            matrix=matrix,
        )
        if translation is None:
            translation = matrix_translation

        local = make_matrix(translation=translation, rotation=rotation)
        self._frames[frame].local = local

        if log:
            self._log(frame, local, static=static)
        return local

    def _log(self, frame: str, local: npt.NDArray[np.float64], *, static: bool) -> None:
        import dalaran as dl

        entity = self._frames[frame].entity_path
        archetype: Any = dl.Transform3D(
            translation=local[:3, 3],
            quaternion=matrix_to_quaternion(local[:3, :3]),
        )
        dl.log(entity, archetype, static=static, recording=self._recording)

    def local(self, frame: str) -> npt.NDArray[np.float64]:
        """Return the frame's current `parent_from_child` transform as a 4x4 matrix."""
        return self.frame(frame).local.copy()

    def path_to_root(self, frame: str) -> list[str]:
        """
        Return the chain of frame names from `frame` up to (and including) the root.

        Examples
        --------
        ```python
        import dalaran as dl

        tree = dl.robot.TransformTree()
        tree.add_chain("base_link", "lidar")
        assert tree.path_to_root("lidar") == ["lidar", "base_link", "world"]
        ```

        """
        chain: list[str] = []
        current: str | None = self.frame(frame).name
        while current is not None:
            chain.append(current)
            current = self._frames[current].parent
        return chain

    def root_from(self, frame: str) -> npt.NDArray[np.float64]:
        """
        Return the transform mapping points in `frame` into the root frame.

        Examples
        --------
        ```python
        import dalaran as dl

        tree = dl.robot.TransformTree()
        tree.set("base_link", parent="world", translation=[1.0, 0.0, 0.0], log=False)
        tree.set("lidar", parent="base_link", translation=[0.0, 0.0, 0.5], log=False)
        assert list(tree.root_from("lidar")[:3, 3]) == [1.0, 0.0, 0.5]
        ```

        """
        chain = self.path_to_root(frame)
        return compose(*[self._frames[name].local for name in reversed(chain)])

    def lookup(self, target: str, source: str) -> npt.NDArray[np.float64]:
        """
        Return `target_from_source`: the 4x4 transform of `source` expressed in `target`.

        This mirrors ROS's `tf2 lookup_transform(target_frame, source_frame)`:
        the returned matrix maps a point expressed in `source` coordinates into
        `target` coordinates, and its translation column is the origin of
        `source` as seen from `target`.

        Parameters
        ----------
        target:
            The frame to express the result in.
        source:
            The frame the result describes.

        Returns
        -------
        numpy.ndarray
            The `(4, 4)` homogeneous `target_from_source` transform.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        tree = dl.robot.TransformTree()
        tree.set("base_link", parent="world", translation=[2.0, 0.0, 0.0], log=False)
        tree.set("lidar", parent="base_link", translation=[0.0, 0.0, 1.0], log=False)

        # The lidar sits 1 m above a base that is 2 m ahead of the world origin.
        np.testing.assert_allclose(tree.lookup("world", "lidar")[:3, 3], [2.0, 0.0, 1.0])
        # ... so from the lidar, the world origin is 2 m back and 1 m down.
        np.testing.assert_allclose(tree.lookup("lidar", "world")[:3, 3], [-2.0, 0.0, -1.0])
        ```

        """
        return compose(invert(self.root_from(target)), self.root_from(source))

    def transform_points(self, points: npt.ArrayLike, source: str, target: str) -> npt.NDArray[np.float64]:
        """
        Re-express `(N, 3)` points from frame `source` into frame `target`.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl

        tree = dl.robot.TransformTree()
        tree.set("base_link", parent="world", translation=[1.0, 0.0, 0.0], log=False)
        np.testing.assert_allclose(
            tree.transform_points([[0.0, 0.0, 0.0]], "base_link", "world"),
            [[1.0, 0.0, 0.0]],
        )
        ```

        """
        from ._math import transform_points as _transform_points

        return _transform_points(self.lookup(target, source), points)

    def __repr__(self) -> str:
        return f"TransformTree(root={self._root!r}, frames={len(self._frames)})"
