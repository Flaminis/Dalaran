#!/usr/bin/env python3
"""
A synthetic nav2 stack: a layered global costmap and a rolling local costmap.

Builds a small warehouse-like map, runs the three costmap layers nav2 would run
over it - static, obstacle and inflation - and drives a robot along a path with a
rolling local costmap window following it, logging everything the way
`dalaran.ros2` logs a real nav2 graph.

Every grid here is in ROS order: `grid[y, x]` with row `0` at the map origin, so
`grid.reshape(-1)` is exactly what a `nav_msgs/OccupancyGrid` would carry in
`data`. The orientation, placement and cost colormapping are then done by the
same functions the ROS 2 bridge uses.
"""

from __future__ import annotations

import argparse

import numpy as np
import numpy.typing as npt

import dalaran as dl
from dalaran.ros2.costmap import (
    COST_INSCRIBED_INFLATED_OBSTACLE,
    COST_LETHAL_OBSTACLE,
    COST_MAX_GRADIENT,
    COST_NO_INFORMATION,
    CostmapLayer,
    RollingCostmapWindow,
    log_costmap_layers,
    rolling_window_origin,
)
from dalaran.ros2.occupancy_grid import occupancy_grid_placement

WIDTH = 120
HEIGHT = 120
RESOLUTION = 0.05
INSCRIBED_RADIUS = 0.18
INFLATION_RADIUS = 0.55
COST_SCALING_FACTOR = 3.0
LOCAL_WINDOW_CELLS = 48


def build_static_map() -> npt.NDArray[np.uint8]:
    """Return the static layer: outer walls and two shelving runs."""
    grid = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    grid[0, :] = grid[-1, :] = COST_LETHAL_OBSTACLE
    grid[:, 0] = grid[:, -1] = COST_LETHAL_OBSTACLE
    grid[25:70, 34:38] = COST_LETHAL_OBSTACLE
    grid[85:89, 20:90] = COST_LETHAL_OBSTACLE
    return grid


def build_obstacle_layer(step: int) -> npt.NDArray[np.uint8]:
    """Return the obstacle layer: one pallet and one person walking a loop."""
    grid = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    grid[46:52, 70:78] = COST_LETHAL_OBSTACLE  # a pallet someone left out

    angle = step / 12.0
    center = (75.0 + 18.0 * np.cos(angle), 40.0 + 18.0 * np.sin(angle))
    ys, xs = np.mgrid[0:HEIGHT, 0:WIDTH]
    person = (xs - center[0]) ** 2 + (ys - center[1]) ** 2 <= 9.0
    grid[person] = COST_LETHAL_OBSTACLE
    return grid


def inflate(lethal: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
    """
    Return the inflation layer for a grid of lethal obstacles.

    This is `nav2_costmap_2d`'s inflation curve: everything within the robot's
    inscribed radius is `INSCRIBED_INFLATED_OBSTACLE`, and beyond that the cost
    decays exponentially out to the inflation radius.
    """
    occupied = lethal >= COST_LETHAL_OBSTACLE
    ys, xs = np.nonzero(occupied)
    if len(xs) == 0:
        return np.zeros_like(lethal)

    grid_y, grid_x = np.mgrid[0:HEIGHT, 0:WIDTH]
    nearest = np.full((HEIGHT, WIDTH), np.inf)
    for start in range(0, len(xs), 256):
        chunk_x = xs[start : start + 256]
        chunk_y = ys[start : start + 256]
        distance = np.sqrt((grid_x[..., None] - chunk_x) ** 2 + (grid_y[..., None] - chunk_y) ** 2)
        nearest = np.minimum(nearest, distance.min(axis=-1))
    meters = nearest * RESOLUTION

    cost = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    decaying = (meters > INSCRIBED_RADIUS) & (meters <= INFLATION_RADIUS)
    falloff = np.exp(-COST_SCALING_FACTOR * (meters[decaying] - INSCRIBED_RADIUS))
    cost[decaying] = np.clip(np.round(COST_MAX_GRADIENT * falloff), 1, COST_MAX_GRADIENT).astype(np.uint8)
    cost[meters <= INSCRIBED_RADIUS] = COST_INSCRIBED_INFLATED_OBSTACLE
    cost[occupied] = COST_LETHAL_OBSTACLE
    return cost


def crop_window(grid: npt.NDArray[np.uint8], center_cell: tuple[int, int]) -> npt.NDArray[np.uint8]:
    """
    Crop a rolling window out of a global grid, centered on `center_cell`.

    Cells outside the global map become `NO_INFORMATION`, which is exactly what a
    real local costmap reports for space it has not observed - and, because
    unknown cells are logged transparent, the global costmap keeps showing through
    there.
    """
    size = LOCAL_WINDOW_CELLS
    x0 = center_cell[0] - size // 2
    y0 = center_cell[1] - size // 2
    window = np.full((size, size), COST_NO_INFORMATION, dtype=np.uint8)

    src_x0, src_y0 = max(x0, 0), max(y0, 0)
    src_x1, src_y1 = min(x0 + size, WIDTH), min(y0 + size, HEIGHT)
    if src_x1 > src_x0 and src_y1 > src_y0:
        window[src_y0 - y0 : src_y1 - y0, src_x0 - x0 : src_x1 - x0] = grid[src_y0:src_y1, src_x0:src_x1]
    return window


def robot_path(steps: int) -> npt.NDArray[np.float64]:
    """Return the `(steps, 2)` path the robot drives, in meters."""
    t = np.linspace(0.0, 1.0, steps)
    x = 0.6 + t * (WIDTH * RESOLUTION - 1.2)
    y = 1.2 + 0.8 * np.sin(t * 2.0 * np.pi)
    return np.stack([x, y], axis=1)


def main() -> None:
    parser = argparse.ArgumentParser(description="A layered nav2 global costmap plus a rolling local costmap.")
    parser.add_argument("--steps", type=int, default=60, help="How many navigation steps to simulate.")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_nav2_costmap")
    dl.log("map", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    static_layer = build_static_map()
    static_inflation = inflate(static_layer)
    placement = occupancy_grid_placement(
        static_layer.reshape(-1),
        width=WIDTH,
        height=HEIGHT,
        resolution=RESOLUTION,
        frame_id="map",
    )

    path = robot_path(args.steps)
    window = RollingCostmapWindow("map/local_costmap")

    for step, position in enumerate(path):
        dl.set_time("step", sequence=step)

        obstacle_layer = build_obstacle_layer(step)
        merged = np.maximum(np.maximum(static_layer, obstacle_layer), static_inflation)
        obstacle_inflation = inflate(obstacle_layer)

        # The global costmap, as the layer stack nav2 actually computes. Each
        # layer is its own entity, drawn in plugin order, and translucent enough
        # that the map underneath stays readable.
        log_costmap_layers(
            "map/global_costmap",
            [
                CostmapLayer("static", static_layer.reshape(-1)),
                CostmapLayer("static_inflation", static_inflation.reshape(-1)),
                CostmapLayer("obstacle", obstacle_layer.reshape(-1)),
                CostmapLayer("obstacle_inflation", obstacle_inflation.reshape(-1)),
            ],
            placement,
        )

        # The local costmap is a window that slides with the robot: one entity,
        # a new pose every step. `RollingCostmapWindow` keeps that straight and
        # refuses to log it as static data.
        center_cell = (int(position[0] / RESOLUTION), int(position[1] / RESOLUTION))
        window_placement = occupancy_grid_placement(
            crop_window(merged, center_cell).reshape(-1),
            width=LOCAL_WINDOW_CELLS,
            height=LOCAL_WINDOW_CELLS,
            resolution=RESOLUTION,
            origin_translation=rolling_window_origin(
                position,
                width=LOCAL_WINDOW_CELLS,
                height=LOCAL_WINDOW_CELLS,
                resolution=RESOLUTION,
            ),
            frame_id="map",
        )
        window.log(
            [CostmapLayer("costmap", crop_window(merged, center_cell).reshape(-1))],
            window_placement,
            base_draw_order=10.0,
        )

        dl.log(
            "map/robot",
            dl.Points3D([[position[0], position[1], 0.0]], radii=INSCRIBED_RADIUS, colors=[(255, 255, 255)]),
        )
        dl.log(
            "map/plan",
            dl.LineStrips3D(
                [np.pad(path[step:], ((0, 0), (0, 1)))],
                colors=[(60, 200, 120)],
                radii=0.03,
            ),
        )

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
