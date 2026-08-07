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
"""

from __future__ import annotations

from typing import Final

import numpy as np
import numpy.typing as npt

__all__ = [
    "FLU",
    "FRD",
    "RDF",
    "RUB",
    "convention_matrix",
    "convert_frame_convention",
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
