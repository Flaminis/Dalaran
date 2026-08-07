"""
Axis conventions for robotics, and conversions between them.

Mixing up axis conventions is the single most common source of "my point cloud
is rotated 90 degrees" bugs in robotics visualization. Dalaran makes the
convention explicit instead of implicit.

A convention is written as a three-letter code describing what the local
**+X, +Y and +Z** axes point at, using the letters:

| Letter | Direction |
| ------ | --------- |
| `F`    | Forward   |
| `B`    | Back      |
| `L`    | Left      |
| `R`    | Right     |
| `U`    | Up        |
| `D`    | Down      |

The two conventions you meet every single day:

* [`FLU`][dalaran.robot.conventions.FLU] - ROS REP-103 body and world frames
  (`x` forward, `y` left, `z` up). This is also what Dalaran's 3D views use by
  default, which is why ROS poses "just work".
* [`RDF`][dalaran.robot.conventions.RDF] - the ROS REP-103 *optical* frame
  (`x` right, `y` down, `z` forward). This is what `camera_optical_frame`,
  OpenCV and every pinhole intrinsics matrix use.

Also provided: [`FRD`][dalaran.robot.conventions.FRD] (aerospace body frame,
used by PX4/ArduPilot) and [`RUB`][dalaran.robot.conventions.RUB] (the OpenGL /
"gltf" camera convention).

Beyond body frames, this module covers the two other things REP-103 and REP-105
standardize and that everybody re-implements slightly wrong:

* **Geographic frames**: [`enu_to_ned`][dalaran.robot.conventions.enu_to_ned] and
  friends convert positions *and* orientations between ROS's east-north-up world
  and the north-east-down world of autopilots and inertial navigation systems.
* **The REP-105 frame chain**: [`Rep105Chain`][dalaran.robot.conventions.Rep105Chain]
  sets up `map -> odom -> base_link` and names its methods after the *node* that
  publishes each transform, so the classic "I published map->base_link" bug is
  hard to write in the first place.
* **Frame naming**: [`infer_convention`][dalaran.robot.conventions.infer_convention]
  and [`explain_convention`][dalaran.robot.conventions.explain_convention] turn
  the REP-103 naming rule (`*_optical_frame` is RDF, everything else is FLU) into
  something you can assert on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
import numpy.typing as npt

from ._math import compose, invert, make_matrix, matrix_to_quaternion, quaternion_to_matrix

if TYPE_CHECKING:
    from dalaran.recording_stream import RecordingStream

    from .frames import TransformTree

__all__ = [
    "BASE_FOOTPRINT_FRAME",
    "BASE_LINK_FRAME",
    "EARTH_FRAME",
    "ENU",
    "FLU",
    "FRD",
    "MAP_FRAME",
    "NED",
    "ODOM_FRAME",
    "OPTICAL_FRAME_SUFFIXES",
    "RDF",
    "REP105_CHAIN",
    "RUB",
    "FrameConvention",
    "Rep105Chain",
    "convention_matrix",
    "convert_frame_convention",
    "enu_ned_matrix",
    "enu_to_ned",
    "enu_to_ned_quaternion",
    "enu_to_ned_rotation_matrix",
    "explain_convention",
    "infer_convention",
    "ned_to_enu",
    "ned_to_enu_quaternion",
    "ned_to_enu_rotation_matrix",
]

FLU: Final = "FLU"
"""ROS REP-103 body/world convention: `x` forward, `y` left, `z` up."""

RDF: Final = "RDF"
"""ROS REP-103 optical / OpenCV camera convention: `x` right, `y` down, `z` forward."""

FRD: Final = "FRD"
"""Aerospace body convention (PX4, ArduPilot): `x` forward, `y` right, `z` down."""

RUB: Final = "RUB"
"""OpenGL / glTF camera convention: `x` right, `y` up, `z` back."""

# Each letter expressed in a canonical right-handed FLU reference basis.
_AXIS_VECTORS: Final[dict[str, tuple[float, float, float]]] = {
    "F": (1.0, 0.0, 0.0),
    "B": (-1.0, 0.0, 0.0),
    "L": (0.0, 1.0, 0.0),
    "R": (0.0, -1.0, 0.0),
    "U": (0.0, 0.0, 1.0),
    "D": (0.0, 0.0, -1.0),
}

_OPPOSITE: Final[dict[str, str]] = {"F": "B", "B": "F", "L": "R", "R": "L", "U": "D", "D": "U"}


def _basis(convention: str) -> npt.NDArray[np.float64]:
    """Return the 3x3 matrix whose columns are the convention's axes in the canonical FLU basis."""
    code = str(convention).strip().upper()
    if len(code) != 3:
        msg = f"An axis convention must be exactly 3 letters, got {convention!r}"
        raise ValueError(msg)

    for letter in code:
        if letter not in _AXIS_VECTORS:
            msg = f"Unknown axis letter {letter!r} in convention {convention!r}; expected one of FBLRUD"
            raise ValueError(msg)

    for a, b in ((code[0], code[1]), (code[0], code[2]), (code[1], code[2])):
        if a == b or _OPPOSITE[a] == b:
            msg = f"Convention {convention!r} is degenerate: {a!r} and {b!r} lie on the same axis"
            raise ValueError(msg)

    basis = np.array([_AXIS_VECTORS[letter] for letter in code], dtype=np.float64).T
    if np.linalg.det(basis) < 0.0:
        msg = f"Convention {convention!r} is left-handed; Dalaran only supports right-handed frames"
        raise ValueError(msg)
    return basis


def convention_matrix(src: str, dst: str) -> npt.NDArray[np.float64]:
    """
    Return the 3x3 rotation that re-expresses a vector from convention `src` in convention `dst`.

    Parameters
    ----------
    src:
        Three-letter source convention, e.g. `"FLU"`.
    dst:
        Three-letter destination convention, e.g. `"RDF"`.

    Returns
    -------
    numpy.ndarray
        A `(3, 3)` orthonormal, right-handed rotation matrix.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    # In an FLU body frame, "one meter forward" is +X ...
    m = conventions.convention_matrix(conventions.FLU, conventions.RDF)
    # ... and in the RDF optical frame that same direction is +Z.
    np.testing.assert_allclose(m @ [1, 0, 0], [0, 0, 1], atol=1e-12)
    ```

    """
    return _basis(dst).T @ _basis(src)


def convert_frame_convention(
    data: npt.ArrayLike,
    src: str,
    dst: str,
) -> npt.NDArray[np.float64]:
    """
    Convert points, vectors or rigid transforms between two axis conventions.

    The input is dispatched on its shape:

    * a `(4, 4)` array is treated as a rigid transform and converted by the
      similarity `R @ T @ R.T`, so the result is the *same* physical transform
      written in the `dst` convention;
    * anything else must have a trailing dimension of 3 and is treated as a
      stack of points/vectors, which are simply rotated.

    Parameters
    ----------
    data:
        `(..., 3)` points/vectors, or a single `(4, 4)` homogeneous transform.
    src:
        The convention `data` is currently expressed in, e.g. `"FLU"`.
    dst:
        The convention to convert to, e.g. `"RDF"`.

    Returns
    -------
    numpy.ndarray
        The converted data, with the same shape as `data` and dtype `float64`.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    # A lidar point 2 m ahead and 1 m to the left of an FLU robot ...
    flu = np.array([[2.0, 1.0, 0.0]])
    # ... seen from the camera's optical (RDF) frame: 1 m to the *left* is -1 m
    # along "right", and 2 m ahead is +2 m along "forward".
    rdf = conventions.convert_frame_convention(flu, conventions.FLU, conventions.RDF)
    np.testing.assert_allclose(rdf, [[-1.0, 0.0, 2.0]], atol=1e-12)
    ```

    """
    rot = convention_matrix(src, dst)
    arr = np.asarray(data, dtype=np.float64)

    if arr.shape == (4, 4):
        homogeneous = np.eye(4, dtype=np.float64)
        homogeneous[:3, :3] = rot
        return homogeneous @ arr @ homogeneous.T

    if arr.ndim == 0 or arr.shape[-1] != 3:
        msg = f"Expected a (4, 4) transform or an array with a trailing dimension of 3, got shape {arr.shape}"
        raise ValueError(msg)

    return arr @ rot.T


# --------------------------------------------------------------------------
# Geographic frames: ENU (REP-103) and NED (aerospace)
# --------------------------------------------------------------------------

ENU: Final = "ENU"
"""REP-103 geographic convention: `x` east, `y` north, `z` up. What ROS uses."""

NED: Final = "NED"
"""Aerospace geographic convention: `x` north, `y` east, `z` down. What autopilots and INS units use."""

_ENU_NED: Final[npt.NDArray[np.float64]] = np.array(
    [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
    dtype=np.float64,
)


def enu_ned_matrix() -> npt.NDArray[np.float64]:
    """
    Return the 3x3 rotation that converts between ENU and NED coordinates.

    The matrix is its own inverse - it is a 180 degree rotation about the
    horizontal axis pointing north-east - so the same matrix converts ENU to NED
    and NED to ENU. That is why there is one matrix and not two.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    m = conventions.enu_ned_matrix()
    np.testing.assert_allclose(m @ m, np.eye(3), atol=1e-12)
    # 3 m east, 4 m north, 5 m up is 4 m north, 3 m east, 5 m down.
    np.testing.assert_allclose(m @ [3, 4, 5], [4, 3, -5], atol=1e-12)
    ```

    """
    return _ENU_NED.copy()


def _geographic(data: npt.ArrayLike, *, body: bool) -> npt.NDArray[np.float64]:
    """Shared implementation of ENU<->NED for points and 4x4 poses (the mapping is an involution)."""
    arr = np.asarray(data, dtype=np.float64)

    if arr.shape == (4, 4):
        world = make_matrix(rotation=_ENU_NED)
        child = make_matrix(rotation=convention_matrix(FRD, FLU)) if body else world
        return compose(world, arr, invert(child))

    if arr.ndim == 0 or arr.shape[-1] != 3:
        msg = f"Expected a (4, 4) pose or an array with a trailing dimension of 3, got shape {arr.shape}"
        raise ValueError(msg)

    return arr @ _ENU_NED.T


def enu_to_ned(data: npt.ArrayLike, *, body: bool = True) -> npt.NDArray[np.float64]:
    """
    Convert positions or poses from an ENU world frame to a NED world frame.

    The input is dispatched on its shape:

    * a `(4, 4)` array is treated as a pose of a robot in the world;
    * anything else must have a trailing dimension of 3 and is treated as a
      stack of points or vectors.

    Parameters
    ----------
    data:
        `(..., 3)` points/vectors in ENU, or a single `(4, 4)` ENU pose.
    body:
        Only used for a `(4, 4)` pose. When `True` (the default) the pose's child
        frame is assumed to be a REP-103 `FLU` body frame, which becomes an
        aerospace `FRD` body frame in the NED world - this is the pairing every
        autopilot uses. Pass `False` when the child frame is itself axis-aligned
        with the world, so that only the world axes are re-expressed.

    Returns
    -------
    numpy.ndarray
        The converted data, with the same shape as `data`.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    # A waypoint 10 m east and 2 m up ...
    np.testing.assert_allclose(conventions.enu_to_ned([10.0, 0.0, 2.0]), [0.0, 10.0, -2.0])

    # ... and a robot that faces east in ENU has a NED heading of 90 degrees.
    pose = np.eye(4)
    yaw_ned = np.arctan2(conventions.enu_to_ned(pose)[1, 0], conventions.enu_to_ned(pose)[0, 0])
    assert yaw_ned == np.pi / 2
    ```

    """
    return _geographic(data, body=body)


def ned_to_enu(data: npt.ArrayLike, *, body: bool = True) -> npt.NDArray[np.float64]:
    """
    Convert positions or poses from a NED world frame to an ENU world frame.

    The exact inverse of [`enu_to_ned`][dalaran.robot.conventions.enu_to_ned];
    see it for the meaning of `body`.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    ned = [[100.0, 20.0, -5.0]]
    np.testing.assert_allclose(conventions.ned_to_enu(ned), [[20.0, 100.0, 5.0]])
    np.testing.assert_allclose(conventions.enu_to_ned(conventions.ned_to_enu(ned)), ned)
    ```

    """
    return _geographic(data, body=body)


def _geographic_rotation(rotation: npt.ArrayLike, *, body: bool) -> npt.NDArray[np.float64]:
    r = np.asarray(rotation, dtype=np.float64)
    if r.shape != (3, 3):
        msg = f"Expected a 3x3 rotation matrix, got shape {r.shape}"
        raise ValueError(msg)
    child = convention_matrix(FRD, FLU) if body else _ENU_NED
    return _ENU_NED @ r @ child.T


def enu_to_ned_rotation_matrix(rotation: npt.ArrayLike, *, body: bool = True) -> npt.NDArray[np.float64]:
    """
    Convert an orientation from ENU to NED, as a 3x3 rotation matrix.

    `rotation` maps body coordinates into ENU world coordinates; the result maps
    the corresponding body coordinates into NED world coordinates. With
    `body=True` the body axes are converted from `FLU` to `FRD` as well, which
    is the pairing REP-103 and every autopilot use together.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    # Facing east in ENU is a heading of 90 degrees in NED.
    ned = conventions.enu_to_ned_rotation_matrix(np.eye(3))
    assert np.arctan2(ned[1, 0], ned[0, 0]) == np.pi / 2
    ```

    """
    return _geographic_rotation(rotation, body=body)


def ned_to_enu_rotation_matrix(rotation: npt.ArrayLike, *, body: bool = True) -> npt.NDArray[np.float64]:
    """
    Convert an orientation from NED to ENU, as a 3x3 rotation matrix.

    The exact inverse of
    [`enu_to_ned_rotation_matrix`][dalaran.robot.conventions.enu_to_ned_rotation_matrix].

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions
    from dalaran.robot._math import euler_to_matrix

    r = euler_to_matrix([0.1, -0.2, 1.3])
    np.testing.assert_allclose(
        conventions.ned_to_enu_rotation_matrix(conventions.enu_to_ned_rotation_matrix(r)),
        r,
        atol=1e-12,
    )
    ```

    """
    return _geographic_rotation(rotation, body=body)


def enu_to_ned_quaternion(xyzw: npt.ArrayLike, *, body: bool = True) -> npt.NDArray[np.float64]:
    """
    Convert an orientation quaternion (`xyzw`) from ENU to NED.

    This is the conversion that turns a ROS `sensor_msgs/Imu` orientation into
    the one a MAVLink autopilot reports, and the one people usually get wrong by
    only negating a component.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    # Identity in ENU (facing east, level) is a 90 degree yaw in NED.
    q = conventions.enu_to_ned_quaternion([0.0, 0.0, 0.0, 1.0])
    np.testing.assert_allclose(q, [0.0, 0.0, np.sin(np.pi / 4), np.cos(np.pi / 4)], atol=1e-12)
    ```

    """
    return matrix_to_quaternion(_geographic_rotation(quaternion_to_matrix(xyzw), body=body))


def ned_to_enu_quaternion(xyzw: npt.ArrayLike, *, body: bool = True) -> npt.NDArray[np.float64]:
    """
    Convert an orientation quaternion (`xyzw`) from NED to ENU.

    The exact inverse of
    [`enu_to_ned_quaternion`][dalaran.robot.conventions.enu_to_ned_quaternion],
    up to the quaternion sign (`q` and `-q` are the same rotation).

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import conventions

    q = np.array([0.0, 0.0, np.sin(np.pi / 4), np.cos(np.pi / 4)])
    np.testing.assert_allclose(conventions.ned_to_enu_quaternion(q), [0, 0, 0, 1], atol=1e-12)
    ```

    """
    return matrix_to_quaternion(_geographic_rotation(quaternion_to_matrix(xyzw), body=body))


# --------------------------------------------------------------------------
# REP-105 frame names and semantics
# --------------------------------------------------------------------------

EARTH_FRAME: Final = "earth"
"""REP-105 `earth`: the ECEF frame that ties several `map` frames together."""

MAP_FRAME: Final = "map"
"""REP-105 `map`: a world-fixed frame. Drift-free but discontinuous - it jumps when localization corrects itself."""

ODOM_FRAME: Final = "odom"
"""REP-105 `odom`: continuous and smooth, but drifts without bound. Safe for local motion, unsafe for long-term goals."""

BASE_LINK_FRAME: Final = "base_link"
"""REP-105 `base_link`: rigidly attached to the robot's body, `FLU` per REP-103."""

BASE_FOOTPRINT_FRAME: Final = "base_footprint"
"""The common (non-normative) ground projection of `base_link` used by 2D navigation stacks."""

OPTICAL_FRAME_SUFFIXES: Final[tuple[str, ...]] = ("_optical_frame", "_optical")
"""Frame-name suffixes that REP-103 declares to be `RDF` (`z` forward) rather than `FLU`."""

REP105_CHAIN: Final[tuple[str, ...]] = (EARTH_FRAME, MAP_FRAME, ODOM_FRAME, BASE_LINK_FRAME)
"""The REP-105 frame chain, from the outermost frame inwards."""


@dataclass(frozen=True)
class FrameConvention:
    """
    The axis convention inferred for a frame name, plus the reasoning behind it.

    Returned by [`explain_convention`][dalaran.robot.conventions.explain_convention].
    """

    frame: str
    """The frame name that was inspected."""

    convention: str
    """The inferred three-letter convention, e.g. `"FLU"` or `"RDF"`."""

    reason: str
    """A human-readable explanation, suitable for a log line or an assertion message."""

    def matrix_to(self, dst: str) -> npt.NDArray[np.float64]:
        """Return the rotation from this frame's convention into `dst`."""
        return convention_matrix(self.convention, dst)

    def __str__(self) -> str:
        return f"{self.frame}: {self.convention} ({self.reason})"


def explain_convention(frame: str) -> FrameConvention:
    """
    Infer a frame's axis convention from its name, and explain the inference.

    REP-103 only states one naming rule, but it is the rule that matters: a
    frame whose name ends in `_optical_frame` uses the optical convention
    (`x` right, `y` down, `z` forward), and every other frame uses `FLU`
    (`x` forward, `y` left, `z` up). This helper applies that rule and hands
    back its reasoning, so you can print it next to a suspicious point cloud.

    Parameters
    ----------
    frame:
        A frame name, e.g. `"camera_link"` or `"camera_color_optical_frame"`.

    Returns
    -------
    FrameConvention
        The inferred convention and the reason for it.

    Examples
    --------
    ```python
    from dalaran.robot import conventions

    optical = conventions.explain_convention("camera_color_optical_frame")
    assert optical.convention == conventions.RDF
    print(optical)  # camera_color_optical_frame: RDF (...)

    assert conventions.explain_convention("velodyne").convention == conventions.FLU
    ```

    """
    name = str(frame).strip()
    bare = name.rsplit("/", 1)[-1].lstrip("/")
    lowered = bare.lower()

    for suffix in OPTICAL_FRAME_SUFFIXES:
        if lowered.endswith(suffix):
            return FrameConvention(
                frame=name,
                convention=RDF,
                reason=(
                    f"the name ends in {suffix!r}, which REP-103 reserves for optical frames: "
                    "x right, y down, z forward (the OpenCV camera convention)"
                ),
            )

    if lowered in {EARTH_FRAME, MAP_FRAME, ODOM_FRAME}:
        return FrameConvention(
            frame=name,
            convention=FLU,
            reason=(
                f"{bare!r} is a REP-105 world frame, and REP-103 fixes world frames to "
                "east-north-up, which is FLU for a robot that faces east"
            ),
        )

    return FrameConvention(
        frame=name,
        convention=FLU,
        reason=("the name does not end in an optical suffix, so REP-103's default applies: x forward, y left, z up"),
    )


def infer_convention(frame: str) -> str:
    """
    Return the axis convention implied by a frame's name: `RDF` for optical frames, `FLU` otherwise.

    Use [`explain_convention`][dalaran.robot.conventions.explain_convention] when
    you also want to know *why*.

    Examples
    --------
    ```python
    from dalaran.robot import conventions

    assert conventions.infer_convention("camera_depth_optical_frame") == conventions.RDF
    assert conventions.infer_convention("base_link") == conventions.FLU
    ```

    """
    return explain_convention(frame).convention


class Rep105Chain:
    """
    The REP-105 `map -> odom -> base_link` chain, with the publishers spelled out.

    REP-105 splits the robot's pose into two transforms that are produced by two
    different nodes:

    | Transform | Published by | Character |
    | --------- | ------------ | --------- |
    | `map -> odom` | localization (AMCL, a SLAM backend, a GPS fuser) | jumps when the estimate is corrected |
    | `odom -> base_link` | odometry (wheel encoders, VIO, an EKF) | smooth and continuous, drifts |

    The classic bug is publishing `map -> base_link` directly, which makes the
    odometry frame meaningless and fights whatever else is on the chain. This
    class makes that hard: the setters are named after the node that owns the
    transform, and if all you have is the robot's pose in `map`, you use
    [`set_pose_in_map`][dalaran.robot.conventions.Rep105Chain.set_pose_in_map],
    which derives the `map -> odom` correction from the current odometry instead
    of short-circuiting it.

    Parameters
    ----------
    tree:
        An existing [`TransformTree`][dalaran.robot.TransformTree] to declare the
        chain in. A new tree rooted at `map_frame` is created when omitted.
    map_frame:
        Name of the world-fixed frame.
    odom_frame:
        Name of the continuous odometry frame.
    base_frame:
        Name of the robot body frame.
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use, when creating a tree.

    Examples
    --------
    ```python
    import numpy as np
    import dalaran as dl

    dl.init("dalaran_example_rep105", spawn=True)

    chain = dl.robot.conventions.Rep105Chain()

    # The odometry node publishes odom -> base_link ...
    chain.set_odometry(translation=[1.0, 0.0, 0.0], rpy=[0.0, 0.0, 0.1])
    # ... and localization publishes the map -> odom correction.
    chain.set_localization(translation=[0.05, -0.02, 0.0])

    # Where is the robot in the map? Ask, do not publish.
    np.testing.assert_allclose(chain.pose_in_map()[:3, 3], [1.05, -0.02, 0.0], atol=1e-9)
    ```

    """

    def __init__(
        self,
        tree: TransformTree | None = None,
        *,
        map_frame: str = MAP_FRAME,
        odom_frame: str = ODOM_FRAME,
        base_frame: str = BASE_LINK_FRAME,
        recording: RecordingStream | None = None,
    ) -> None:
        from .frames import TransformTree as _TransformTree

        self.map_frame = map_frame
        """The world-fixed frame; `map -> odom` belongs to localization."""

        self.odom_frame = odom_frame
        """The continuous odometry frame; `odom -> base_link` belongs to odometry."""

        self.base_frame = base_frame
        """The robot body frame."""

        self.tree = tree if tree is not None else _TransformTree(root=map_frame, recording=recording)
        """The [`TransformTree`][dalaran.robot.TransformTree] the chain lives in."""

        for name, parent in ((map_frame, None), (odom_frame, map_frame), (base_frame, odom_frame)):
            if name not in self.tree:
                if parent is None:
                    msg = f"Frame {name!r} is not in the given tree; pass a tree rooted at {name!r}"
                    raise KeyError(msg)
                self.tree.add(name, parent)

    def set_localization(
        self,
        *,
        translation: npt.ArrayLike | None = None,
        quaternion: npt.ArrayLike | None = None,
        rotation_matrix: npt.ArrayLike | None = None,
        rpy: npt.ArrayLike | None = None,
        matrix: npt.ArrayLike | None = None,
    ) -> npt.NDArray[np.float64]:
        """
        Publish `map -> odom`: the correction a localization node applies to the odometry.

        This is **not** the robot's pose. It is the accumulated drift that
        localization has measured, and it is normally close to identity at the
        start of a run.
        """
        return self.tree.set(
            self.odom_frame,
            translation=translation,
            quaternion=quaternion,
            rotation_matrix=rotation_matrix,
            rpy=rpy,
            matrix=matrix,
        )

    def set_odometry(
        self,
        *,
        translation: npt.ArrayLike | None = None,
        quaternion: npt.ArrayLike | None = None,
        rotation_matrix: npt.ArrayLike | None = None,
        rpy: npt.ArrayLike | None = None,
        matrix: npt.ArrayLike | None = None,
    ) -> npt.NDArray[np.float64]:
        """
        Publish `odom -> base_link`: the robot's pose according to dead reckoning.

        This is what a `nav_msgs/Odometry` message with `header.frame_id == "odom"`
        contains, and it is the transform that must stay smooth.
        """
        return self.tree.set(
            self.base_frame,
            translation=translation,
            quaternion=quaternion,
            rotation_matrix=rotation_matrix,
            rpy=rpy,
            matrix=matrix,
        )

    def set_pose_in_map(self, matrix: npt.ArrayLike) -> npt.NDArray[np.float64]:
        """
        Publish a corrected robot pose *without* short-circuiting the odometry frame.

        Given `map_from_base` - which is what a global localization system
        actually estimates - this computes and publishes the `map -> odom`
        correction that makes the existing `odom -> base_link` odometry agree
        with it: `map_from_odom = map_from_base @ odom_from_base^-1`.

        Parameters
        ----------
        matrix:
            The `(4, 4)` `map_from_base` pose.

        Returns
        -------
        numpy.ndarray
            The published `(4, 4)` `map_from_odom` correction.

        Examples
        --------
        ```python
        import numpy as np
        import dalaran as dl
        from dalaran.robot._math import make_matrix

        dl.init("dalaran_example_rep105_correction", spawn=True)
        chain = dl.robot.conventions.Rep105Chain()

        chain.set_odometry(translation=[10.0, 0.0, 0.0])  # odometry drifted 0.5 m short
        chain.set_pose_in_map(make_matrix(translation=[10.5, 0.0, 0.0]))

        np.testing.assert_allclose(chain.pose_in_map()[:3, 3], [10.5, 0.0, 0.0], atol=1e-9)
        ```

        """
        map_from_base = np.asarray(matrix, dtype=np.float64)
        if map_from_base.shape != (4, 4):
            msg = f"`matrix` must be a (4, 4) map_from_base pose, got shape {map_from_base.shape}"
            raise ValueError(msg)
        odom_from_base = self.tree.local(self.base_frame)
        return self.set_localization(matrix=compose(map_from_base, invert(odom_from_base)))

    def pose_in_map(self) -> npt.NDArray[np.float64]:
        """Return `map_from_base`: the robot's pose in the map frame, composed from the chain."""
        return self.tree.lookup(self.map_frame, self.base_frame)

    def pose_in_odom(self) -> npt.NDArray[np.float64]:
        """Return `odom_from_base`: the robot's pose according to odometry alone."""
        return self.tree.lookup(self.odom_frame, self.base_frame)

    def localization_correction(self) -> npt.NDArray[np.float64]:
        """Return the current `map_from_odom` correction, i.e. the drift localization has absorbed."""
        return self.tree.lookup(self.map_frame, self.odom_frame)

    def attach(self, frame: str, parent: str | None = None) -> str:
        """
        Declare a sensor frame on the robot and return the convention implied by its name.

        Examples
        --------
        ```python
        import dalaran as dl

        chain = dl.robot.conventions.Rep105Chain()
        assert chain.attach("camera_color_optical_frame") == dl.robot.conventions.RDF
        assert chain.attach("velodyne") == dl.robot.conventions.FLU
        ```

        """
        self.tree.add(frame, self.base_frame if parent is None else parent)
        return infer_convention(frame)

    def __repr__(self) -> str:
        return f"Rep105Chain(map={self.map_frame!r}, odom={self.odom_frame!r}, base={self.base_frame!r})"
