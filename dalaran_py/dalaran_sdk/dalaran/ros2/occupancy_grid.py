"""
`nav_msgs/OccupancyGrid` -> a correctly oriented, colormapped [`dalaran.GridMap`][].

Occupancy grids are the single easiest ROS message to get subtly wrong: the
cell array is stored bottom-up (row `0` sits at the map origin), while image
buffers are top-down, and the grid's pose describes the *lower-left corner* of
the map rather than its center. This module does that bookkeeping once.

The orientation and origin math lives in pure functions that take and return
numpy arrays, so it can be tested without ROS or a Dalaran recording.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

__all__ = [
    "OCCUPANCY_UNKNOWN",
    "GridPlacement",
    "occupancy_grid_placement",
    "occupancy_to_rgba",
]

#: The `int8` value `nav_msgs/OccupancyGrid` uses for "not observed yet".
OCCUPANCY_UNKNOWN = -1

# The RViz "map" palette, reimplemented so the numpy path matches the viewer's
# `Colormap.RvizMap` shader exactly.
_UNKNOWN_COLOR = (112, 137, 134)


@dataclass
class GridPlacement:
    """
    An occupancy grid, ready to hand to [`dalaran.GridMap`][].

    Attributes
    ----------
    cells:
        `(height, width)` uint8 image buffer in *top-down* order, preserving the
        ROS byte convention where `-1` (unknown) round-trips to `255`.
    cell_size:
        Size of one cell in meters, i.e. the message's `info.resolution`.
    translation:
        `(3,)` position of the grid's lower-left corner in its parent frame.
    quaternion:
        `(4,)` orientation of the grid's lower-left corner as `xyzw`.
    width:
        Number of cells along the grid's local +x axis.
    height:
        Number of cells along the grid's local +y axis.
    frame_id:
        The `header.frame_id` the grid is expressed in, when known.

    """

    cells: npt.NDArray[np.uint8]
    cell_size: float
    translation: npt.NDArray[np.float64]
    quaternion: npt.NDArray[np.float64]
    width: int
    height: int
    frame_id: str = ""

    @property
    def extent(self) -> tuple[float, float]:
        """The grid's `(width, height)` in meters."""
        return (self.width * self.cell_size, self.height * self.cell_size)


def occupancy_grid_placement(
    data: npt.ArrayLike,
    *,
    width: int,
    height: int,
    resolution: float,
    origin_translation: npt.ArrayLike = (0.0, 0.0, 0.0),
    origin_quaternion: npt.ArrayLike = (0.0, 0.0, 0.0, 1.0),
    frame_id: str = "",
) -> GridPlacement:
    """
    Turn raw `nav_msgs/OccupancyGrid` contents into an oriented image buffer plus pose.

    ROS stores the cells row-major with `data[y * width + x]`, and cell `(0, 0)`
    lives at the grid's *origin* pose, so the array grows upwards in the grid's
    local +y. Image buffers grow downwards, so the rows are reversed here; the
    grid's origin pose then describes the lower-left corner of the resulting
    image, which is exactly what [`dalaran.GridMap`][] wants.

    Cell values are kept in ROS's own byte encoding: `0..=100` is the occupancy
    probability and `-1` becomes `255`, so `dalaran.components.Colormap.RvizMap`
    renders unknown space distinctly from free space instead of collapsing both
    to white.

    Parameters
    ----------
    data:
        The message's `data`, a length `width * height` array of `int8`.
    width:
        `info.width`, the number of cells along the grid's local +x.
    height:
        `info.height`, the number of cells along the grid's local +y.
    resolution:
        `info.resolution`, the size of a cell in meters.
    origin_translation:
        `info.origin.position` as `(x, y, z)`.
    origin_quaternion:
        `info.origin.orientation` as `(x, y, z, w)`.
    frame_id:
        The frame the grid is expressed in, for bookkeeping.

    Returns
    -------
    GridPlacement
        The oriented buffer and the pose of its lower-left corner.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.occupancy_grid import occupancy_grid_placement

    # A 2x2 map whose only occupied cell is at grid coordinate (1, 0),
    # i.e. the bottom-right cell.
    placement = occupancy_grid_placement(
        [0, 100, -1, 0],
        width=2,
        height=2,
        resolution=0.5,
        origin_translation=(-1.0, -1.0, 0.0),
    )
    # Row 0 of an image buffer is the *top* row, so it holds the grid's last row.
    np.testing.assert_array_equal(placement.cells, [[255, 0], [0, 100]])
    assert placement.extent == (1.0, 1.0)
    ```

    """
    width = int(width)
    height = int(height)
    if width < 0 or height < 0:
        msg = "OccupancyGrid width and height must be non-negative"
        raise ValueError(msg)

    cells = np.asarray(data)
    if cells.dtype != np.int8:
        cells = cells.astype(np.int8, casting="unsafe")
    expected = width * height
    if cells.size != expected:
        msg = f"OccupancyGrid has {cells.size} cells but info says {width}x{height} = {expected}"
        raise ValueError(msg)

    # `-1 -> 255` on purpose: the RViz map palette keys off the raw byte.
    grid = cells.reshape(height, width).view(np.uint8)
    # Do not "fix" this flip away. `dalaran.GridMap.translation` is the pose of the
    # map's LOWER-LEFT corner, but the image buffer it holds is top-row-first: the
    # viewer places buffer row 0 at `+y = height * cell_size` and grows downwards
    # (`crates/viewer/dl_view_spatial/src/visualizers/grid_map.rs`, the `NEG_Y`
    # extent). ROS stores `data[y * width + x]` with row 0 at the origin, i.e.
    # bottom-first, so the rows have to be reversed. Dalaran's own Rust lens does
    # exactly the same thing in `ros_map_buffer_to_image_buffer`
    # (`crates/store/dl_lenses/src/semantic/ros2msg/ros_map_helpers.rs`:
    # `for image_row in (0..row_height).rev()`), and this keeps the Python bridge
    # byte-for-byte identical to it.
    buffer = np.ascontiguousarray(grid[::-1])

    translation = np.asarray(origin_translation, dtype=np.float64).reshape(-1)
    if translation.size == 2:
        translation = np.append(translation, 0.0)
    if translation.size != 3:
        msg = "origin_translation must have 2 or 3 components"
        raise ValueError(msg)

    quaternion = np.asarray(origin_quaternion, dtype=np.float64).reshape(-1)
    if quaternion.size != 4:
        msg = "origin_quaternion must be (x, y, z, w)"
        raise ValueError(msg)
    norm = float(np.linalg.norm(quaternion))
    quaternion = np.array([0.0, 0.0, 0.0, 1.0]) if norm == 0.0 else quaternion / norm

    return GridPlacement(
        cells=buffer,
        cell_size=float(resolution),
        translation=translation,
        quaternion=quaternion,
        width=width,
        height=height,
        frame_id=frame_id,
    )


def occupancy_to_rgba(
    cells: npt.ArrayLike,
    *,
    free_color: tuple[int, int, int] = (255, 255, 255),
    occupied_color: tuple[int, int, int] = (0, 0, 0),
    unknown_color: tuple[int, int, int] = _UNKNOWN_COLOR,
    unknown_alpha: int = 255,
) -> npt.NDArray[np.uint8]:
    """
    Colorize occupancy cells explicitly, as `(..., 4)` uint8 RGBA.

    Use this when you want the map baked into an ordinary [`dalaran.Image`][],
    or when you want unknown space to be transparent so another layer shows
    through. The default palette matches RViz: free space is white, occupied
    space is black, and unknown space is a distinct teal-gray that can never be
    confused with either.

    Parameters
    ----------
    cells:
        Occupancy values, either signed (`-1..=100`) or in ROS's byte encoding
        where `255` means unknown. Any shape is accepted; a trailing RGBA axis
        is appended.
    free_color:
        RGB for a cell with occupancy `0`.
    occupied_color:
        RGB for a cell with occupancy `100`.
    unknown_color:
        RGB for unknown cells.
    unknown_alpha:
        Alpha for unknown cells. Set to `0` to make unobserved space see-through.

    Returns
    -------
    numpy.ndarray
        `(..., 4)` uint8 RGBA.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.occupancy_grid import occupancy_to_rgba

    rgba = occupancy_to_rgba([[0, 100, -1]])
    np.testing.assert_array_equal(rgba[0, 0], [255, 255, 255, 255])  # free
    np.testing.assert_array_equal(rgba[0, 1], [0, 0, 0, 255])  # occupied
    assert rgba[0, 2, 0] != rgba[0, 1, 0]  # unknown is its own color
    ```

    """
    values = np.asarray(cells)
    if values.dtype == np.uint8:
        signed = values.astype(np.int16)
        signed = np.where(signed > 127, signed - 256, signed)
    else:
        signed = values.astype(np.int16)

    unknown = signed < 0
    probability = np.clip(signed, 0, 100).astype(np.float64) / 100.0

    free = np.asarray(free_color, dtype=np.float64)
    occupied = np.asarray(occupied_color, dtype=np.float64)
    ramp = free + probability[..., None] * (occupied - free)

    out = np.empty((*signed.shape, 4), dtype=np.uint8)
    out[..., :3] = np.round(ramp).astype(np.uint8)
    out[..., 3] = 255
    out[unknown, :3] = np.asarray(unknown_color, dtype=np.uint8)
    out[unknown, 3] = np.uint8(unknown_alpha)
    return out
