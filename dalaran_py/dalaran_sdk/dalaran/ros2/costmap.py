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
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .occupancy_grid import occupancy_grid_placement

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy.typing as npt

    from .occupancy_grid import GridPlacement

__all__ = [
    "COST_FREE",
    "COST_INSCRIBED_INFLATED_OBSTACLE",
    "COST_LETHAL_OBSTACLE",
    "COST_MAX_GRADIENT",
    "COST_NO_INFORMATION",
    "DALARAN_COST_PALETTE",
    "DEFAULT_DRAW_ORDER_STEP",
    "DEFAULT_UPPER_LAYER_OPACITY",
    "RVIZ_COST_PALETTE",
    "CostPalette",
    "CostScale",
    "CostmapLayer",
    "PlannedLayer",
    "RollingCostmapWindow",
    "WindowShift",
    "costmap_layer_rgba",
    "costmap_to_rgba",
    "log_costmap_layers",
    "normalize_cost_values",
    "occupancy_byte_to_raw_cost",
    "plan_costmap_layers",
    "raw_cost_to_occupancy_byte",
    "rolling_window_origin",
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


# -- layered costmaps -------------------------------------------------------

#: Opacity given to a stacked layer that does not ask for one of its own.
#:
#: The bottom layer stays fully opaque and everything above it is translucent, so
#: an operator can see the static map through the obstacle and inflation layers
#: that refine it.
DEFAULT_UPPER_LAYER_OPACITY = 0.7

#: How much `draw_order` each layer gains over the one below it.
DEFAULT_DRAW_ORDER_STEP = 1.0


@dataclass(frozen=True)
class CostmapLayer:
    """
    One layer of a nav2 costmap: `static`, `obstacle`, `inflation`, `voxel`, ...

    A layer holds cost values in the message's own bottom-up order; the placement
    it is logged with supplies the pose, resolution and dimensions, since every
    layer of one costmap shares the same grid.

    Attributes
    ----------
    name:
        The layer's name, which becomes the last part of its entity path.
    cells:
        Cost values in ROS order (`data[y * width + x]`, row `0` at the origin),
        either flat or already `(height, width)`.
    scale:
        Which cost spelling `cells` uses. See [`CostScale`][dalaran.ros2.costmap.CostScale].
    palette:
        Colors for this layer.
    opacity:
        Explicit opacity in `[0, 1]`. `None` means "opaque if this is the bottom
        layer, [`DEFAULT_UPPER_LAYER_OPACITY`][dalaran.ros2.costmap.DEFAULT_UPPER_LAYER_OPACITY]
        otherwise".
    draw_order:
        Explicit draw order. `None` means "one step above the layer below me".

    Examples
    --------
    ```python
    from dalaran.ros2.costmap import CostmapLayer

    static = CostmapLayer("static", [0, 0, 254, 0])
    inflation = CostmapLayer("inflation", [0, 200, 253, 200], opacity=0.5)
    assert inflation.opacity == 0.5
    ```

    """

    name: str
    cells: npt.ArrayLike
    scale: CostScale = "raw"
    palette: CostPalette = RVIZ_COST_PALETTE
    opacity: float | None = None
    draw_order: float | None = None


@dataclass(frozen=True)
class PlannedLayer:
    """
    Where and how one [`CostmapLayer`][dalaran.ros2.costmap.CostmapLayer] should be logged.

    Produced by [`plan_costmap_layers`][dalaran.ros2.costmap.plan_costmap_layers]. It
    exists so that the stacking rules - entity paths, draw order and opacity - are a
    pure function that can be asserted on without logging anything.

    Attributes
    ----------
    layer:
        The layer this plan is for.
    entity_path:
        The entity path the layer belongs on.
    draw_order:
        The layer's `draw_order`; higher values render on top.
    opacity:
        The layer's resolved opacity in `[0, 1]`.

    """

    layer: CostmapLayer
    entity_path: str
    draw_order: float
    opacity: float


def plan_costmap_layers(
    layers: Sequence[CostmapLayer],
    *,
    entity_path: str = "costmap",
    base_draw_order: float = 0.0,
    draw_order_step: float = DEFAULT_DRAW_ORDER_STEP,
    upper_layer_opacity: float = DEFAULT_UPPER_LAYER_OPACITY,
) -> list[PlannedLayer]:
    """
    Resolve entity paths, draw order and opacity for a stack of costmap layers.

    `layers` is ordered bottom-up, exactly like a `nav2_costmap_2d` plugin list: the
    static map first, then the obstacle and voxel layers that add sensor data, then
    the inflation layer on top. Each layer gets its own entity below `entity_path`,
    so a layer can be toggled, styled or blueprint-selected on its own, and a
    monotonically increasing `draw_order` so the viewer stacks them in that order
    rather than in whatever order the chunks happen to arrive.

    Parameters
    ----------
    layers:
        The layers, bottom-most first.
    entity_path:
        The entity path the stack lives under.
    base_draw_order:
        `draw_order` for the bottom layer.
    draw_order_step:
        How much each layer gains over the one below it.
    upper_layer_opacity:
        Opacity for layers above the bottom one that do not set their own.

    Returns
    -------
    list of PlannedLayer
        One plan per layer, in the given order.

    Raises
    ------
    ValueError
        If two layers would land on the same entity path, which would silently make
        one overwrite the other.

    Examples
    --------
    ```python
    from dalaran.ros2.costmap import CostmapLayer, plan_costmap_layers

    plans = plan_costmap_layers(
        [CostmapLayer("static", [0]), CostmapLayer("inflation", [0])],
        entity_path="map/global_costmap",
    )
    assert [plan.entity_path for plan in plans] == [
        "map/global_costmap/static",
        "map/global_costmap/inflation",
    ]
    assert plans[1].draw_order > plans[0].draw_order
    assert plans[0].opacity == 1.0  # the base layer stays fully opaque
    assert plans[1].opacity < 1.0  # you can see the base layer through it
    ```

    """
    from .naming import entity_path_join, sanitize_path_part

    plans: list[PlannedLayer] = []
    seen: set[str] = set()
    for index, layer in enumerate(layers):
        name = sanitize_path_part(layer.name) or f"layer{index}"
        path = entity_path_join(entity_path, name)
        if path in seen:
            msg = f"Two costmap layers both map to the entity path {path!r}; give them distinct names"
            raise ValueError(msg)
        seen.add(path)

        draw_order = layer.draw_order
        if draw_order is None:
            draw_order = base_draw_order + index * draw_order_step

        opacity = layer.opacity
        if opacity is None:
            opacity = 1.0 if index == 0 else upper_layer_opacity

        plans.append(
            PlannedLayer(
                layer=layer,
                entity_path=path,
                draw_order=float(draw_order),
                opacity=float(np.clip(opacity, 0.0, 1.0)),
            )
        )
    return plans


def costmap_layer_rgba(layer: CostmapLayer, placement: GridPlacement) -> npt.NDArray[np.uint8]:
    """
    Colorize one layer into a top-down `(height, width, 4)` RGBA buffer.

    The row flip and the dimension check are delegated to
    [`occupancy_grid_placement`][dalaran.ros2.occupancy_grid.occupancy_grid_placement],
    so a layer is oriented by exactly the same code as the map it is stacked on and
    cannot drift out of alignment with it.

    Parameters
    ----------
    layer:
        The layer to colorize.
    placement:
        The placement every layer of this costmap shares, which supplies the
        dimensions and resolution.

    Returns
    -------
    numpy.ndarray
        `(height, width, 4)` uint8 RGBA in image order.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.costmap import CostmapLayer, costmap_layer_rgba
    from dalaran.ros2.occupancy_grid import occupancy_grid_placement

    placement = occupancy_grid_placement([0, 0, 0, 0], width=2, height=2, resolution=0.05)
    # Cost 254 sits at ROS (x=0, y=0), i.e. the bottom-left of the image.
    rgba = costmap_layer_rgba(CostmapLayer("obstacle", [254, 0, 0, 0]), placement)
    np.testing.assert_array_equal(rgba[1, 0], [255, 0, 255, 255])
    assert rgba[0, 0, 3] == 0  # free space stays see-through
    ```

    """
    oriented = occupancy_grid_placement(
        layer.cells,
        width=placement.width,
        height=placement.height,
        resolution=placement.cell_size,
    ).cells
    return costmap_to_rgba(oriented, scale=layer.scale, palette=layer.palette)


def log_costmap_layers(
    entity_path: str,
    layers: Sequence[CostmapLayer],
    placement: GridPlacement,
    *,
    ctx: Any = None,
    recording: Any = None,
    static: bool = False,
    base_draw_order: float = 0.0,
    draw_order_step: float = DEFAULT_DRAW_ORDER_STEP,
    upper_layer_opacity: float = DEFAULT_UPPER_LAYER_OPACITY,
) -> list[str]:
    """
    Log a stack of costmap layers as separate, correctly ordered [`dalaran.GridMap`][]s.

    Every layer shares one `placement`, so they line up exactly; each gets its own
    entity, its own `draw_order` and its own `opacity`. The buffers are RGBA rather
    than single-channel-plus-colormap because per-cell alpha is what lets an upper
    layer's free and unknown cells stay see-through - without it, an inflation layer
    would paint over the static map it is supposed to annotate.

    Parameters
    ----------
    entity_path:
        The entity path the stack lives under.
    layers:
        The layers, bottom-most first.
    placement:
        The shared placement, normally from
        [`occupancy_grid_placement`][dalaran.ros2.occupancy_grid.occupancy_grid_placement].
    ctx:
        An optional [`dalaran.ros2.Context`][] to log through. The ROS 2 converters
        pass theirs; call sites outside the bridge can leave this unset.
    recording:
        The [`dalaran.RecordingStream`][] to log to when `ctx` is not given.
    static:
        Log the layers as static data.
    base_draw_order:
        `draw_order` for the bottom layer.
    draw_order_step:
        How much each layer gains over the one below it.
    upper_layer_opacity:
        Opacity for layers above the bottom one that do not set their own.

    Returns
    -------
    list of str
        The entity path each layer was logged to, bottom-most first.

    Examples
    --------
    ```python
    import dalaran as dl
    from dalaran.ros2.costmap import CostmapLayer, log_costmap_layers
    from dalaran.ros2.occupancy_grid import occupancy_grid_placement

    dl.init("dalaran_example_costmap_layers", spawn=True)

    placement = occupancy_grid_placement([0] * 16, width=4, height=4, resolution=0.05)
    log_costmap_layers(
        "map/global_costmap",
        [
            CostmapLayer("static", [0, 0, 254, 0] * 4),
            CostmapLayer("inflation", [0, 200, 253, 200] * 4),
        ],
        placement,
    )
    ```

    """
    import dalaran as dl

    plans = plan_costmap_layers(
        layers,
        entity_path=entity_path,
        base_draw_order=base_draw_order,
        draw_order_step=draw_order_step,
        upper_layer_opacity=upper_layer_opacity,
    )

    for plan in plans:
        rgba = costmap_layer_rgba(plan.layer, placement)
        grid_map = dl.GridMap(
            data=rgba.tobytes(),
            format=dl.components.ImageFormat(
                width=placement.width,
                height=placement.height,
                color_model="RGBA",
                channel_datatype="U8",
            ),
            cell_size=placement.cell_size,
            translation=placement.translation,
            quaternion=placement.quaternion,
            opacity=plan.opacity,
            draw_order=plan.draw_order,
        )
        if ctx is not None:
            ctx.log(plan.entity_path, grid_map, static=static)
        else:
            dl.log(plan.entity_path, grid_map, static=static, recording=recording)

    return [plan.entity_path for plan in plans]


# -- rolling local costmaps -------------------------------------------------


def rolling_window_origin(
    center: npt.ArrayLike,
    *,
    width: int,
    height: int,
    resolution: float,
    snap_to_cells: bool = True,
) -> npt.NDArray[np.float64]:
    """
    Return the lower-left origin of a rolling window centered on `center`.

    A `nav2_costmap_2d` configured with `rolling_window: true` keeps the robot in
    the middle of a fixed-size grid, so its origin moves with every update. nav2
    snaps that origin to whole cells, because a sub-cell shift would force it to
    resample the whole grid; reproducing the snap here keeps a hand-built window
    aligned with the one nav2 would have published.

    Parameters
    ----------
    center:
        The point to center the window on, usually the robot's `(x, y)` in the
        window's parent frame. A third component is passed through untouched.
    width:
        Window width in cells.
    height:
        Window height in cells.
    resolution:
        Cell size in meters.
    snap_to_cells:
        Snap the origin down to a multiple of `resolution`.

    Returns
    -------
    numpy.ndarray
        `(3,)` position of the window's lower-left corner.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.costmap import rolling_window_origin

    origin = rolling_window_origin((10.0, 4.0), width=60, height=60, resolution=0.05)
    np.testing.assert_allclose(origin, [8.5, 2.5, 0.0])
    ```

    """
    point = np.asarray(center, dtype=np.float64).reshape(-1)
    if point.size == 2:
        point = np.append(point, 0.0)
    if point.size != 3:
        msg = "center must have 2 or 3 components"
        raise ValueError(msg)

    resolution = float(resolution)
    origin = point.copy()
    origin[0] -= int(width) * resolution / 2.0
    origin[1] -= int(height) * resolution / 2.0
    if snap_to_cells and resolution > 0.0:
        origin[:2] = np.floor(origin[:2] / resolution) * resolution
    return origin


@dataclass(frozen=True)
class WindowShift:
    """
    How far a rolling costmap window moved between two messages.

    Attributes
    ----------
    moved:
        Whether the origin changed at all. `False` for the very first update.
    meters:
        `(dx, dy)` translation of the window's lower-left corner, in meters.
    cells:
        The same shift in whole cells, rounded. A window that moved by an exact
        number of cells has reused its old contents; a fractional shift means the
        publisher resampled, which is worth noticing when data looks smeared.
    resized:
        Whether the window's dimensions or resolution changed, which invalidates
        any comparison between the two grids.

    """

    moved: bool
    meters: tuple[float, float]
    cells: tuple[int, int]
    resized: bool


class RollingCostmapWindow:
    """
    Tracks the moving origin of a rolling local costmap on one stable entity.

    The gotcha this exists to prevent: `/local_costmap/costmap` is a small window
    that *slides* with the robot, so its `info.origin` is different in almost every
    message while the grid itself keeps the same size. The entity path must stay
    constant - the local costmap is one thing that moves, not a new thing per
    frame - and the pose must be re-logged on every message rather than logged once
    as static data. Logging it statically, or deriving the entity path from the
    origin, are the two ways this goes wrong: the first freezes the window at its
    first origin while its contents keep updating, and the second litters the entity
    tree with thousands of one-frame entities that never get cleared.

    Parameters
    ----------
    entity_path:
        The single entity path this window is logged to, for its whole lifetime.

    Examples
    --------
    ```python
    from dalaran.ros2.costmap import RollingCostmapWindow
    from dalaran.ros2.occupancy_grid import occupancy_grid_placement

    window = RollingCostmapWindow("map/local_costmap")
    first = occupancy_grid_placement([0] * 4, width=2, height=2, resolution=0.5)
    assert not window.update(first).moved

    # The robot drove one cell east; same entity, new pose.
    second = occupancy_grid_placement(
        [0] * 4, width=2, height=2, resolution=0.5, origin_translation=(0.5, 0.0, 0.0)
    )
    shift = window.update(second)
    assert shift.moved
    assert shift.cells == (1, 0)
    ```

    """

    def __init__(self, entity_path: str) -> None:
        self.entity_path = entity_path
        self.placement: GridPlacement | None = None

    def update(self, placement: GridPlacement) -> WindowShift:
        """
        Record a new message's placement and report how the window moved.

        Parameters
        ----------
        placement:
            The placement built from the incoming message.

        Returns
        -------
        WindowShift
            The movement since the previous message.

        """
        previous = self.placement
        self.placement = placement
        if previous is None:
            return WindowShift(moved=False, meters=(0.0, 0.0), cells=(0, 0), resized=False)

        delta = (
            np.asarray(placement.translation, dtype=np.float64)[:2]
            - np.asarray(previous.translation, dtype=np.float64)[:2]
        )
        cell_size = placement.cell_size
        cells = np.round(delta / cell_size).astype(int) if cell_size > 0.0 else np.zeros(2, dtype=int)
        resized = (previous.width, previous.height, previous.cell_size) != (
            placement.width,
            placement.height,
            placement.cell_size,
        )
        return WindowShift(
            moved=bool(np.any(delta != 0.0)),
            meters=(float(delta[0]), float(delta[1])),
            cells=(int(cells[0]), int(cells[1])),
            resized=resized,
        )

    def log(
        self,
        layers: Sequence[CostmapLayer],
        placement: GridPlacement,
        *,
        ctx: Any = None,
        recording: Any = None,
        **kwargs: Any,
    ) -> WindowShift:
        """
        Update the window and log `layers` at its stable entity path.

        `static` is deliberately not accepted: a rolling window's pose changes every
        message, so logging it statically would pin it to its first origin forever.

        Parameters
        ----------
        layers:
            The window's layers, bottom-most first.
        placement:
            The placement built from the incoming message.
        ctx:
            An optional [`dalaran.ros2.Context`][] to log through.
        recording:
            The [`dalaran.RecordingStream`][] to log to when `ctx` is not given.
        kwargs:
            Forwarded to [`log_costmap_layers`][dalaran.ros2.costmap.log_costmap_layers].

        Returns
        -------
        WindowShift
            How far the window moved since the previous message.

        """
        shift = self.update(placement)
        log_costmap_layers(
            self.entity_path,
            layers,
            placement,
            ctx=ctx,
            recording=recording,
            static=False,
            **kwargs,
        )
        return shift
