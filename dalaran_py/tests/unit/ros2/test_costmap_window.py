"""Tests for the rolling local costmap window: moving origin, stable entity."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from dalaran.ros2.costmap import CostmapLayer, RollingCostmapWindow, rolling_window_origin
from dalaran.ros2.occupancy_grid import occupancy_grid_placement


def window_placement(origin: tuple[float, float], *, resolution: float = 0.5) -> Any:
    return occupancy_grid_placement(
        [0] * 4,
        width=2,
        height=2,
        resolution=resolution,
        origin_translation=origin,
    )


def test_a_rolling_window_is_centered_on_the_robot() -> None:
    origin = rolling_window_origin((10.0, 4.0), width=60, height=60, resolution=0.05)
    np.testing.assert_allclose(origin, [8.5, 2.5, 0.0])


def test_the_origin_snaps_to_whole_cells_like_nav2_does() -> None:
    # nav2 refuses to place a window origin between cells, because that would
    # force it to resample the entire grid on every update.
    origin = rolling_window_origin((0.07, 0.0), width=2, height=2, resolution=0.05)
    np.testing.assert_allclose(origin[:2], [0.0, -0.05])
    assert np.allclose(np.remainder(origin[:2], 0.05), 0.0)


def test_snapping_can_be_turned_off() -> None:
    origin = rolling_window_origin((0.07, 0.0), width=2, height=2, resolution=0.05, snap_to_cells=False)
    np.testing.assert_allclose(origin[:2], [0.02, -0.05])


def test_the_first_message_reports_no_movement() -> None:
    window = RollingCostmapWindow("map/local_costmap")
    shift = window.update(window_placement((0.0, 0.0)))
    assert not shift.moved
    assert shift.cells == (0, 0)


def test_a_moving_window_reports_its_shift_in_cells() -> None:
    window = RollingCostmapWindow("map/local_costmap")
    window.update(window_placement((0.0, 0.0)))
    shift = window.update(window_placement((1.5, -0.5)))
    assert shift.moved
    assert shift.cells == (3, -1)
    assert shift.meters == pytest.approx((1.5, -0.5))
    assert not shift.resized


def test_a_resized_window_is_flagged() -> None:
    window = RollingCostmapWindow("map/local_costmap")
    window.update(window_placement((0.0, 0.0), resolution=0.5))
    assert window.update(window_placement((0.0, 0.0), resolution=0.25)).resized


def test_the_entity_path_never_changes_while_the_pose_does(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    window = RollingCostmapWindow("map/local_costmap")
    layers = [CostmapLayer("obstacle", [0, 0, 254, 0])]

    for step in range(3):
        window.log(layers, window_placement((0.5 * step, 0.0)), ctx=ctx)

    # One entity, three poses: the local costmap is one thing that moves, not a
    # new thing per frame.
    assert set(captured.paths) == {"map/local_costmap/obstacle"}
    translations = [record.archetypes[0].kwargs["translation"][0] for record in captured.logs]
    np.testing.assert_allclose(translations, [0.0, 0.5, 1.0])


def test_a_rolling_window_is_never_logged_as_static(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    # Static data would pin the window to its first origin forever while its
    # contents kept updating.
    window = RollingCostmapWindow("map/local_costmap")
    window.log([CostmapLayer("obstacle", [0] * 4)], window_placement((0.0, 0.0)), ctx=ctx)
    assert all(not record.static for record in captured.logs)


def test_the_window_remembers_the_latest_placement() -> None:
    window = RollingCostmapWindow("map/local_costmap")
    assert window.placement is None
    placement = window_placement((2.0, 3.0))
    window.update(placement)
    assert window.placement is placement
