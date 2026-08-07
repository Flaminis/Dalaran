"""
nav2 costmap semantics: cost values, palettes and layered rendering.

A ROS costmap is *not* an occupancy grid with a different name. `nav_msgs/OccupancyGrid`
stores an occupancy probability in `0..=100`, while a `nav2_costmap_2d` grid stores a
*cost* in `0..=255` with three reserved values at the top of the range:

| value    | meaning                                                       |
| -------- | ------------------------------------------------------------- |
| `0`      | free space                                                     |
| `1..=252`| increasing cost, usually the inflation layer's decay curve     |
| `253`    | `INSCRIBED_INFLATED_OBSTACLE`: the robot's inscribed circle collides |
| `254`    | `LETHAL_OBSTACLE`: definitely occupied                          |
| `255`    | `NO_INFORMATION`: never observed                                |

The `253`/`254` values are *categories*, not "very high cost". Drawing them anywhere on
the cost gradient is the classic costmap visualization bug: an inflated-obstacle ring
ends up looking like "cost 200" and an operator cannot tell whether the planner refused
to enter a cell because it would collide or merely because it was expensive. Every
palette in this module therefore renders the three reserved values in their own hues,
off the gradient entirely.

nav2 publishes the same data in two spellings. `nav2_msgs/msg/Costmap` carries the raw
`0..=255` cost, while `/global_costmap/costmap` and `/local_costmap/costmap` are
`nav_msgs/OccupancyGrid` messages whose values have been squeezed through
`costmap_2d`'s cost translation table into `0..=100` with `-1` for unknown. Both are
handled here, and [`occupancy_byte_to_raw_cost`][dalaran.ros2.costmap.occupancy_byte_to_raw_cost]
lifts the squeezed spelling back to real cost semantics so a single palette covers both.

Everything in this module is a pure function over numpy arrays. Nothing here logs, so
the cost boundaries can be tested without ROS, a viewer or a recording.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

__all__ = [
    "COST_FREE",
    "COST_INSCRIBED_INFLATED_OBSTACLE",
    "COST_LETHAL_OBSTACLE",
    "COST_MAX_GRADIENT",
    "COST_NO_INFORMATION",
    "DALARAN_COST_PALETTE",
    "RVIZ_COST_PALETTE",
    "CostPalette",
    "CostScale",
    "costmap_to_rgba",
    "normalize_cost_values",
    "occupancy_byte_to_raw_cost",
    "raw_cost_to_occupancy_byte",
]

#: Zero cost: the planner may drive here freely.
COST_FREE = 0

#: The highest value that is an actual cost rather than a reserved category.
COST_MAX_GRADIENT = 252

#: `nav2_costmap_2d`'s `INSCRIBED_INFLATED_OBSTACLE`: the robot's inscribed circle
#: would collide here, so the cell is lethal for any orientation.
COST_INSCRIBED_INFLATED_OBSTACLE = 253

#: `nav2_costmap_2d`'s `LETHAL_OBSTACLE`: an actual observed obstacle.
COST_LETHAL_OBSTACLE = 254

#: `nav2_costmap_2d`'s `NO_INFORMATION`, spelled `-1` on `nav_msgs/OccupancyGrid` topics.
COST_NO_INFORMATION = 255

#: Which of nav2's two on-the-wire cost spellings an array uses.
#:
#: `"raw"` is `nav2_msgs/msg/Costmap`'s `0..=255`; `"occupancy"` is the
#: `costmap_2d` translation table's `0..=100` plus `-1`, as published on
#: `nav_msgs/OccupancyGrid` costmap topics.
CostScale = Literal["raw", "occupancy"]

# `costmap_2d::Costmap2DPublisher` builds its translation table as
# `1 + (97 * (i - 1)) / 251` for `i` in `1..=252`, mapping the cost gradient onto
# `1..=98` and leaving `99`/`100` free for the two reserved obstacle categories.
_TRANSLATED_GRADIENT_MAX = 98
_TRANSLATED_INSCRIBED = 99
_TRANSLATED_LETHAL = 100


@dataclass(frozen=True)
class CostPalette:
    """
    Colors for the four semantic classes of a nav2 cost value.

    The gradient covers `1..=252` only. The reserved values get their own solid
    colors so that "would collide" and "expensive" can never be confused, and both
    free and unknown space default to fully transparent so a costmap layer can be
    stacked on top of the static map it refines.

    Attributes
    ----------
    low:
        RGB for cost `1`, the cheapest non-free cell.
    high:
        RGB for cost `252`, the most expensive non-reserved cell.
    inscribed:
        RGB for `253`, `INSCRIBED_INFLATED_OBSTACLE`.
    lethal:
        RGB for `254`, `LETHAL_OBSTACLE`.
    unknown:
        RGB for `255`, `NO_INFORMATION`.
    free_alpha:
        Alpha for cost `0`. Zero, so free space shows the layer below.
    gradient_alpha:
        Alpha for the `1..=252` gradient.
    unknown_alpha:
        Alpha for `255`. Zero, so an unobserved cell in an upper layer shows the
        layer below rather than blanking it out.

    Examples
    --------
    ```python
    from dalaran.ros2.costmap import RVIZ_COST_PALETTE, CostPalette

    # A palette that paints unknown space instead of leaving it see-through.
    opaque_unknown = CostPalette(**{**vars(RVIZ_COST_PALETTE), "unknown_alpha": 255})
    assert opaque_unknown.inscribed == RVIZ_COST_PALETTE.inscribed
    ```

    """

    low: tuple[int, int, int] = (0, 0, 255)
    high: tuple[int, int, int] = (255, 0, 0)
    inscribed: tuple[int, int, int] = (0, 255, 255)
    lethal: tuple[int, int, int] = (255, 0, 255)
    unknown: tuple[int, int, int] = (112, 137, 134)
    free_alpha: int = 0
    gradient_alpha: int = 255
    unknown_alpha: int = 0


#: RViz's costmap palette: blue to red cost, cyan inscribed, magenta lethal.
RVIZ_COST_PALETTE = CostPalette()

#: The Dalaran palette, matching [`dalaran.components.Colormap.Costmap`][]: green to
#: yellow cost, red inscribed, blue lethal.
DALARAN_COST_PALETTE = CostPalette(
    low=(134, 217, 166),
    high=(246, 218, 117),
    inscribed=(215, 47, 33),
    lethal=(24, 106, 221),
)


def normalize_cost_values(cells: npt.ArrayLike) -> npt.NDArray[np.uint8]:
    """
    Return `cells` as unsigned bytes, folding the signed `-1` spelling onto `255`.

    ROS hands the same costmap over as `int8` (where unknown is `-1`) or as `uint8`
    (where unknown is `255`), depending on which message type carried it. Everything
    downstream wants one spelling, and `255` is the one nav2 itself uses.

    Parameters
    ----------
    cells:
        Cost values in any integer dtype and any shape.

    Returns
    -------
    numpy.ndarray
        The same shape, as `uint8`.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.costmap import normalize_cost_values

    np.testing.assert_array_equal(normalize_cost_values([-1, 0, 100]), [255, 0, 100])
    ```

    """
    values = np.asarray(cells)
    if values.dtype == np.uint8:
        return values
    return np.asarray(values).astype(np.int64).astype(np.uint8, casting="unsafe")


def raw_cost_to_occupancy_byte(cells: npt.ArrayLike) -> npt.NDArray[np.uint8]:
    """
    Squeeze raw `0..=255` costs into `costmap_2d`'s `0..=100` publishing scale.

    This reproduces `costmap_2d::Costmap2DPublisher`'s cost translation table
    exactly: the `1..=252` gradient is compressed onto `1..=98`, `253` becomes `99`,
    `254` becomes `100` and `255` stays `255` (i.e. `-1` once reinterpreted as
    `int8`). Use it when you want a raw `nav2_msgs/Costmap` rendered by the viewer's
    native [`dalaran.components.Colormap.RvizCostmap`][] or
    [`dalaran.components.Colormap.Costmap`][], which both key off that scale.

    Parameters
    ----------
    cells:
        Raw cost values, `0..=255`.

    Returns
    -------
    numpy.ndarray
        `uint8` values on the `0..=100` scale, with `255` preserved for unknown.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.costmap import raw_cost_to_occupancy_byte

    translated = raw_cost_to_occupancy_byte([0, 1, 252, 253, 254, 255])
    np.testing.assert_array_equal(translated, [0, 1, 98, 99, 100, 255])
    ```

    """
    values = normalize_cost_values(cells).astype(np.int64)
    gradient = 1 + (97 * (values - 1)) // 251
    out = np.select(
        [
            values == COST_FREE,
            values == COST_INSCRIBED_INFLATED_OBSTACLE,
            values == COST_LETHAL_OBSTACLE,
            values == COST_NO_INFORMATION,
        ],
        [0, _TRANSLATED_INSCRIBED, _TRANSLATED_LETHAL, COST_NO_INFORMATION],
        default=np.clip(gradient, 1, _TRANSLATED_GRADIENT_MAX),
    )
    return out.astype(np.uint8)


def occupancy_byte_to_raw_cost(cells: npt.ArrayLike) -> npt.NDArray[np.uint8]:
    """
    Lift `costmap_2d`'s published `0..=100` scale back to raw `0..=255` cost.

    `/global_costmap/costmap` and `/local_costmap/costmap` are `nav_msgs/OccupancyGrid`
    topics, so the costs on them have already been squeezed. Undoing the squeeze
    restores the *categories* - `99` is `INSCRIBED_INFLATED_OBSTACLE` and `100` is
    `LETHAL_OBSTACLE`, not "99% and 100% occupied" - which is what lets one palette
    serve both message types.

    Parameters
    ----------
    cells:
        Values on the `0..=100` scale, with unknown spelled either `-1` or `255`.

    Returns
    -------
    numpy.ndarray
        `uint8` raw costs.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.costmap import occupancy_byte_to_raw_cost

    raw = occupancy_byte_to_raw_cost([0, 1, 98, 99, 100, -1])
    np.testing.assert_array_equal(raw, [0, 1, 252, 253, 254, 255])
    ```

    """
    values = normalize_cost_values(cells).astype(np.int64)
    gradient = 1 + (251 * (values - 1)) // 97
    out = np.select(
        [
            values == 0,
            values == _TRANSLATED_INSCRIBED,
            values == _TRANSLATED_LETHAL,
            values > _TRANSLATED_LETHAL,
        ],
        [
            0,
            COST_INSCRIBED_INFLATED_OBSTACLE,
            COST_LETHAL_OBSTACLE,
            COST_NO_INFORMATION,
        ],
        default=np.clip(gradient, 1, COST_MAX_GRADIENT),
    )
    return out.astype(np.uint8)


def costmap_to_rgba(
    cells: npt.ArrayLike,
    *,
    scale: CostScale = "raw",
    palette: CostPalette = RVIZ_COST_PALETTE,
) -> npt.NDArray[np.uint8]:
    """
    Colorize nav2 cost values as `(..., 4)` uint8 RGBA.

    The `1..=252` gradient interpolates from `palette.low` to `palette.high`. The
    reserved values are drawn in their own solid colors, so an inflated-obstacle ring
    is never mistakable for a merely expensive cell. Free and unknown cells are
    transparent by default, which is what makes a stack of costmap layers readable:
    the static map stays visible through the inflation layer's empty space.

    Parameters
    ----------
    cells:
        Cost values of any shape, signed or unsigned.
    scale:
        `"raw"` for `nav2_msgs/Costmap`'s `0..=255`, or `"occupancy"` for the
        `0..=100` values published on `nav_msgs/OccupancyGrid` costmap topics.
    palette:
        The colors to use. See [`RVIZ_COST_PALETTE`][dalaran.ros2.costmap.RVIZ_COST_PALETTE]
        and [`DALARAN_COST_PALETTE`][dalaran.ros2.costmap.DALARAN_COST_PALETTE].

    Returns
    -------
    numpy.ndarray
        `(..., 4)` uint8 RGBA, ready for an RGBA [`dalaran.GridMap`][].

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.costmap import costmap_to_rgba

    rgba = costmap_to_rgba([0, 128, 253, 254, 255])
    assert rgba[0, 3] == 0  # free space is see-through
    assert rgba[4, 3] == 0  # so is never-observed space
    np.testing.assert_array_equal(rgba[2], [0, 255, 255, 255])  # inscribed
    np.testing.assert_array_equal(rgba[3], [255, 0, 255, 255])  # lethal
    # The reserved colors are nowhere on the gradient.
    assert tuple(rgba[1][:3]) not in {(0, 255, 255), (255, 0, 255)}
    ```

    """
    values = normalize_cost_values(cells)
    if scale == "occupancy":
        values = occupancy_byte_to_raw_cost(values)
    elif scale != "raw":
        msg = f"scale must be 'raw' or 'occupancy', not {scale!r}"
        raise ValueError(msg)

    wide = values.astype(np.float64)
    t = np.clip((wide - 1.0) / float(COST_MAX_GRADIENT - 1), 0.0, 1.0)
    low = np.asarray(palette.low, dtype=np.float64)
    high = np.asarray(palette.high, dtype=np.float64)
    ramp = low + t[..., None] * (high - low)

    out = np.empty((*values.shape, 4), dtype=np.uint8)
    out[..., :3] = np.round(ramp).astype(np.uint8)
    out[..., 3] = np.uint8(palette.gradient_alpha)

    free = values == COST_FREE
    out[free, :3] = np.asarray(palette.low, dtype=np.uint8)
    out[free, 3] = np.uint8(palette.free_alpha)

    inscribed = values == COST_INSCRIBED_INFLATED_OBSTACLE
    out[inscribed, :3] = np.asarray(palette.inscribed, dtype=np.uint8)
    out[inscribed, 3] = np.uint8(255)

    lethal = values == COST_LETHAL_OBSTACLE
    out[lethal, :3] = np.asarray(palette.lethal, dtype=np.uint8)
    out[lethal, 3] = np.uint8(255)

    unknown = values == COST_NO_INFORMATION
    out[unknown, :3] = np.asarray(palette.unknown, dtype=np.uint8)
    out[unknown, 3] = np.uint8(palette.unknown_alpha)
    return out
