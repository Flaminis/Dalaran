"""Tests for stacking nav2 costmap layers: paths, draw order, opacity, transparency."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from dalaran.ros2.costmap import (
    DEFAULT_UPPER_LAYER_OPACITY,
    CostmapLayer,
    costmap_layer_rgba,
    log_costmap_layers,
    plan_costmap_layers,
)
from dalaran.ros2.occupancy_grid import occupancy_grid_placement

#: A nav2 plugin stack, bottom-up, on a shared 2x2 grid.
LAYERS = [
    CostmapLayer("static", [0, 0, 254, 0]),
    CostmapLayer("obstacle", [0, 254, 0, 0]),
    CostmapLayer("inflation", [200, 253, 200, 255]),
]


@pytest.fixture
def placement() -> Any:
    return occupancy_grid_placement([0] * 4, width=2, height=2, resolution=0.05)


def test_each_layer_gets_its_own_entity_below_the_costmap() -> None:
    plans = plan_costmap_layers(LAYERS, entity_path="map/global_costmap")
    assert [plan.entity_path for plan in plans] == [
        "map/global_costmap/static",
        "map/global_costmap/obstacle",
        "map/global_costmap/inflation",
    ]


def test_draw_order_increases_from_the_bottom_layer_upwards() -> None:
    orders = [plan.draw_order for plan in plan_costmap_layers(LAYERS)]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(orders)


def test_an_explicit_draw_order_wins_over_the_automatic_one() -> None:
    layers = [CostmapLayer("static", [0]), CostmapLayer("inflation", [0], draw_order=42.0)]
    plans = plan_costmap_layers(layers)
    assert plans[1].draw_order == 42.0


def test_the_base_layer_is_opaque_and_the_ones_above_it_are_not() -> None:
    plans = plan_costmap_layers(LAYERS)
    assert plans[0].opacity == 1.0
    assert plans[1].opacity == pytest.approx(DEFAULT_UPPER_LAYER_OPACITY)
    assert plans[2].opacity == pytest.approx(DEFAULT_UPPER_LAYER_OPACITY)


def test_a_layer_can_set_its_own_opacity_and_it_is_clamped() -> None:
    plans = plan_costmap_layers([CostmapLayer("static", [0], opacity=3.0)])
    assert plans[0].opacity == 1.0


def test_layer_names_are_sanitized_into_path_parts() -> None:
    plans = plan_costmap_layers([CostmapLayer("obstacle layer/v2", [0])], entity_path="costmap")
    assert plans[0].entity_path.startswith("costmap/")
    assert plans[0].entity_path.count("/") == 1


def test_two_layers_with_the_same_name_are_rejected() -> None:
    with pytest.raises(ValueError, match="distinct names"):
        plan_costmap_layers([CostmapLayer("inflation", [0]), CostmapLayer("inflation", [0])])


def test_a_layer_is_oriented_exactly_like_the_map_it_stacks_on(placement: Any) -> None:
    # Cost 254 at ROS (x=0, y=0) is the bottom-left cell, i.e. the LAST buffer row.
    rgba = costmap_layer_rgba(CostmapLayer("obstacle", [254, 0, 0, 0]), placement)
    assert rgba.shape == (2, 2, 4)
    np.testing.assert_array_equal(rgba[1, 0], [255, 0, 255, 255])
    assert rgba[0, 0, 3] == 0


def test_unknown_cells_in_an_upper_layer_are_transparent(placement: Any) -> None:
    # This is the whole point of layering: NO_INFORMATION in the inflation layer
    # must let the static map below show through instead of blanking it out.
    # ROS row 1 is [255, 200], and it ends up as buffer row 0 (the top row).
    rgba = costmap_layer_rgba(CostmapLayer("inflation", [255, 255, 255, 200]), placement)
    assert rgba[..., 3].tolist() == [[0, 255], [0, 0]]


def test_logging_a_stack_emits_one_grid_map_per_layer(_fake_dl: Any, ctx: Any, captured: Any, placement: Any) -> None:
    paths = log_costmap_layers("map/global_costmap", LAYERS, placement, ctx=ctx)

    assert paths == captured.paths
    assert captured.names() == ["GridMap", "GridMap", "GridMap"]
    grid_maps = [record.archetypes[0] for record in captured.logs]

    # Stacked bottom-up, and all sharing one placement so they stay aligned.
    orders = [grid_map.kwargs["draw_order"] for grid_map in grid_maps]
    assert orders == sorted(orders)
    for grid_map in grid_maps:
        assert grid_map.kwargs["cell_size"] == pytest.approx(0.05)
        np.testing.assert_allclose(grid_map.kwargs["translation"], [0.0, 0.0, 0.0])

    assert grid_maps[0].kwargs["opacity"] == 1.0
    assert grid_maps[2].kwargs["opacity"] == pytest.approx(DEFAULT_UPPER_LAYER_OPACITY)


def test_layers_are_logged_as_rgba_so_alpha_survives(_fake_dl: Any, ctx: Any, captured: Any, placement: Any) -> None:
    log_costmap_layers("costmap", [LAYERS[2]], placement, ctx=ctx)
    grid_map = captured.first("GridMap")
    image_format = grid_map.kwargs["format"]
    assert image_format.kwargs["color_model"] == "RGBA"
    # Four bytes per cell, not one: a colormapped single channel cannot express
    # "this cell is unobserved, show me what is underneath".
    assert len(grid_map.kwargs["data"]) == 2 * 2 * 4
