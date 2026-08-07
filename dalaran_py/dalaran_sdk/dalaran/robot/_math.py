"""
Pure-numpy rigid-transform math used by the [`dalaran.robot`][] helpers.

This module deliberately has **no** dependency on the rest of the Dalaran SDK so
that the math can be unit-tested (and reused) without a viewer or a native
extension module being available.

All rotations are right-handed. Quaternions are stored in `xyzw` order, which is
the order used by [`dalaran.datatypes.Quaternion`][] and by ROS.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

__all__ = [
    "compose",
    "euler_to_matrix",
    "identity",
    "invert",
    "make_matrix",
    "matrix_to_euler",
    "matrix_to_quaternion",
    "quaternion_to_matrix",
    "resolve_rotation",
    "transform_points",
]


def identity() -> npt.NDArray[np.float64]:
    """
    Return a 4x4 identity transform.

    Examples
    --------
    ```python
    from dalaran.robot._math import identity

    assert (identity() == np.eye(4)).all()
    ```

    """
    return np.eye(4, dtype=np.float64)


def normalize_quaternion(xyzw: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Return `xyzw` scaled to unit length.

    Parameters
    ----------
    xyzw:
        Quaternion in `(x, y, z, w)` order.

    Raises
    ------
    ValueError
        If the quaternion has (near) zero norm.

    """
    q = np.asarray(xyzw, dtype=np.float64).reshape(4)
    norm = float(np.linalg.norm(q))
    if norm < 1e-12:
        msg = "Cannot normalize a zero-length quaternion"
        raise ValueError(msg)
    return q / norm


def quaternion_to_matrix(xyzw: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Convert a quaternion in `(x, y, z, w)` order to a 3x3 rotation matrix.

    Parameters
    ----------
    xyzw:
        Quaternion in `(x, y, z, w)` order. It is normalized internally, so it
        does not need to be a unit quaternion.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import quaternion_to_matrix

    # 90 degrees about +Z maps +X onto +Y.
    r = quaternion_to_matrix([0.0, 0.0, np.sin(np.pi / 4), np.cos(np.pi / 4)])
    np.testing.assert_allclose(r @ [1, 0, 0], [0, 1, 0], atol=1e-12)
    ```

    """
    x, y, z, w = normalize_quaternion(xyzw)
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def matrix_to_quaternion(matrix: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Convert a 3x3 (or 4x4) rotation matrix to a unit quaternion in `(x, y, z, w)` order.

    Uses the numerically stable branch-on-largest-diagonal formulation, so it is
    well behaved for rotations near 180 degrees.

    Parameters
    ----------
    matrix:
        A 3x3 rotation matrix, or a 4x4 homogeneous matrix whose rotation part is used.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import matrix_to_quaternion, quaternion_to_matrix

    q = np.array([0.0, 0.0, 1.0, 0.0])  # 180 degrees about +Z
    np.testing.assert_allclose(matrix_to_quaternion(quaternion_to_matrix(q)), q, atol=1e-9)
    ```

    """
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape == (4, 4):
        m = m[:3, :3]
    if m.shape != (3, 3):
        msg = f"Expected a 3x3 or 4x4 matrix, got shape {m.shape}"
        raise ValueError(msg)

    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0.0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (m[2, 1] - m[1, 2]) * s
        y = (m[0, 2] - m[2, 0]) * s
        z = (m[1, 0] - m[0, 1]) * s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s

    q = np.array([x, y, z, w], dtype=np.float64)
    if q[3] < 0.0:
        # Pick the canonical hemisphere (w >= 0) so round-trips are stable.
        q = -q
    return normalize_quaternion(q)


def euler_to_matrix(rpy: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Convert fixed-axis roll/pitch/yaw angles (radians) to a 3x3 rotation matrix.

    This uses the REP-103 / URDF convention: extrinsic rotations about the fixed
    X (roll), then Y (pitch), then Z (yaw) axes, i.e. `R = Rz(yaw) @ Ry(pitch) @ Rx(roll)`.
    This is identical to intrinsic Z-Y-X.

    Parameters
    ----------
    rpy:
        `(roll, pitch, yaw)` in radians.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import euler_to_matrix

    # Yaw of 90 degrees turns "forward" (+X) into "left" (+Y).
    r = euler_to_matrix([0.0, 0.0, np.pi / 2])
    np.testing.assert_allclose(r @ [1, 0, 0], [0, 1, 0], atol=1e-12)
    ```

    """
    roll, pitch, yaw = np.asarray(rpy, dtype=np.float64).reshape(3)
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)

    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]], dtype=np.float64)
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], dtype=np.float64)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], dtype=np.float64)
    return rz @ ry @ rx


def matrix_to_euler(matrix: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Convert a rotation matrix to fixed-axis `(roll, pitch, yaw)` angles in radians.

    This is the exact inverse of [`euler_to_matrix`][dalaran.robot._math.euler_to_matrix]
    away from gimbal lock. At gimbal lock (`|pitch| == pi/2`) roll is set to zero
    and the remaining rotation is folded into yaw, which is the usual convention.

    Parameters
    ----------
    matrix:
        A 3x3 rotation matrix, or a 4x4 homogeneous matrix whose rotation part is used.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import euler_to_matrix, matrix_to_euler

    rpy = [0.1, -0.2, 2.9]
    np.testing.assert_allclose(matrix_to_euler(euler_to_matrix(rpy)), rpy, atol=1e-12)
    ```

    """
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape == (4, 4):
        m = m[:3, :3]
    if m.shape != (3, 3):
        msg = f"Expected a 3x3 or 4x4 matrix, got shape {m.shape}"
        raise ValueError(msg)

    sp = -m[2, 0]
    sp = min(1.0, max(-1.0, float(sp)))
    pitch = np.arcsin(sp)
    if abs(sp) > 1.0 - 1e-10:
        # Gimbal lock: only (roll -/+ yaw) is observable, so attribute it all to yaw.
        # For both pitch = +pi/2 and pitch = -pi/2 the residual rotation shows up
        # as `m[0, 1] = -sin(yaw)` and `m[1, 1] = cos(yaw)` once roll is pinned to zero.
        roll = 0.0
        yaw = np.arctan2(-m[0, 1], m[1, 1])
    else:
        roll = np.arctan2(m[2, 1], m[2, 2])
        yaw = np.arctan2(m[1, 0], m[0, 0])
    return np.array([roll, pitch, yaw], dtype=np.float64)


def make_matrix(
    translation: npt.ArrayLike | None = None,
    rotation: npt.ArrayLike | None = None,
) -> npt.NDArray[np.float64]:
    """
    Build a 4x4 homogeneous transform from a translation and a 3x3 rotation.

    Parameters
    ----------
    translation:
        `(3,)` translation, defaults to the origin.
    rotation:
        `(3, 3)` rotation matrix, defaults to identity.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import make_matrix

    t = make_matrix(translation=[1, 2, 3])
    np.testing.assert_allclose(t[:3, 3], [1, 2, 3])
    ```

    """
    out = np.eye(4, dtype=np.float64)
    if rotation is not None:
        r = np.asarray(rotation, dtype=np.float64)
        if r.shape != (3, 3):
            msg = f"Expected a 3x3 rotation matrix, got shape {r.shape}"
            raise ValueError(msg)
        out[:3, :3] = r
    if translation is not None:
        out[:3, 3] = np.asarray(translation, dtype=np.float64).reshape(3)
    return out


def compose(*matrices: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Compose 4x4 transforms left-to-right, i.e. `compose(a, b) == a @ b`.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import compose, make_matrix

    a = make_matrix(translation=[1, 0, 0])
    b = make_matrix(translation=[0, 2, 0])
    np.testing.assert_allclose(compose(a, b)[:3, 3], [1, 2, 0])
    ```

    """
    out = identity()
    for m in matrices:
        mat = np.asarray(m, dtype=np.float64)
        if mat.shape != (4, 4):
            msg = f"Expected a 4x4 matrix, got shape {mat.shape}"
            raise ValueError(msg)
        out = out @ mat
    return out


def invert(matrix: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Invert a 4x4 *rigid* transform analytically (transpose the rotation).

    This is both faster and more accurate than a general matrix inverse, but it
    assumes the rotation block is orthonormal (no scale, no shear).

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import compose, euler_to_matrix, invert, make_matrix

    t = make_matrix(translation=[1, 2, 3], rotation=euler_to_matrix([0.3, 0.2, 0.1]))
    np.testing.assert_allclose(compose(invert(t), t), np.eye(4), atol=1e-12)
    ```

    """
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape != (4, 4):
        msg = f"Expected a 4x4 matrix, got shape {m.shape}"
        raise ValueError(msg)
    r_t = m[:3, :3].T
    out = np.eye(4, dtype=np.float64)
    out[:3, :3] = r_t
    out[:3, 3] = -r_t @ m[:3, 3]
    return out


def transform_points(matrix: npt.ArrayLike, points: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Apply a 4x4 homogeneous transform to an `(N, 3)` array of points.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot._math import make_matrix, transform_points

    t = make_matrix(translation=[0, 0, 1])
    np.testing.assert_allclose(transform_points(t, [[0, 0, 0]]), [[0, 0, 1]])
    ```

    """
    m = np.asarray(matrix, dtype=np.float64)
    p = np.asarray(points, dtype=np.float64)
    single = p.ndim == 1
    p = np.atleast_2d(p)
    if p.shape[-1] != 3:
        msg = f"Expected points with a trailing dimension of 3, got shape {p.shape}"
        raise ValueError(msg)
    out = p @ m[:3, :3].T + m[:3, 3]
    return out[0] if single else out


def resolve_rotation(
    *,
    quaternion: npt.ArrayLike | None = None,
    rotation_matrix: npt.ArrayLike | None = None,
    rpy: npt.ArrayLike | None = None,
    matrix: npt.ArrayLike | None = None,
) -> tuple[npt.NDArray[np.float64] | None, npt.NDArray[np.float64] | None]:
    """
    Normalize the four supported rotation spellings into `(rotation_matrix, translation)`.

    Exactly zero or one of the keyword arguments may be given. Only `matrix`
    (a 4x4 homogeneous transform) contributes a translation; for every other
    spelling the returned translation is `None`.

    Returns
    -------
    tuple
        `(rotation_matrix_or_None, translation_or_None)`.

    Raises
    ------
    ValueError
        If more than one rotation spelling is provided.

    """
    provided = {
        "quaternion": quaternion,
        "rotation_matrix": rotation_matrix,
        "rpy": rpy,
        "matrix": matrix,
    }
    given = [name for name, value in provided.items() if value is not None]
    if len(given) > 1:
        msg = f"Expected at most one rotation argument, got {sorted(given)}"
        raise ValueError(msg)

    if quaternion is not None:
        return quaternion_to_matrix(quaternion), None
    if rotation_matrix is not None:
        r = np.asarray(rotation_matrix, dtype=np.float64)
        if r.shape != (3, 3):
            msg = f"`rotation_matrix` must be 3x3, got shape {r.shape}"
            raise ValueError(msg)
        return r, None
    if rpy is not None:
        return euler_to_matrix(rpy), None
    if matrix is not None:
        m = np.asarray(matrix, dtype=np.float64)
        if m.shape != (4, 4):
            msg = f"`matrix` must be 4x4, got shape {m.shape}"
            raise ValueError(msg)
        return m[:3, :3].copy(), m[:3, 3].copy()
    return None, None
