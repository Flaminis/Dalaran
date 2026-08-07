"""Unit tests for `nav_msgs/OccupancyGrid` orientation, origin and unknown-cell handling."""

from __future__ import annotations

import numpy as np
import pytest
from dalaran.ros2.occupancy_grid import occupancy_grid_placement, occupancy_to_rgba


def test_row_zero_of_the_message_ends_up_at_the_bottom_of_the_buffer() -> None:
    # A deliberately asymmetric L: the vertical stroke runs up the left column
    # and the foot runs along the bottom row, i.e. along ROS row 0.
    #
    #   ROS grid coordinates (x right, y up):
    #     y=2  X . .
    #     y=1  X . .
    #     y=0  X X X
    grid = np.array(
        [
            [100, 100, 100],  # y = 0, the row that sits at the grid origin
            [100, 0, 0],  # y = 1
            [100, 0, 0],  # y = 2
        ],
        dtype=np.int8,
    )
    placement = occupancy_grid_placement(grid.reshape(-1), width=3, height=3, resolution=0.1)

    # `dalaran.GridMap` puts buffer row 0 at the TOP, so the foot of the L, which
    # is at y = 0 in the map, must be the LAST row of the buffer.
    np.testing.assert_array_equal(placement.cells[-1], [100, 100, 100])
    np.testing.assert_array_equal(placement.cells[0], [100, 0, 0])
    # The vertical stroke stays in column 0 either way.
    np.testing.assert_array_equal(placement.cells[:, 0], [100, 100, 100])


def test_a_single_occupied_cell_lands_at_the_right_buffer_position() -> None:
    # Occupy exactly the cell at grid (x=2, y=0), i.e. bottom-right.
    data = np.zeros(3 * 4, dtype=np.int8)
    data[0 * 4 + 2] = 100
    placement = occupancy_grid_placement(data, width=4, height=3, resolution=0.05)

    occupied = np.argwhere(placement.cells == 100)
    # Bottom row of the buffer (row index height - 1), column 2.
    np.testing.assert_array_equal(occupied, [[2, 2]])


def test_unknown_cells_keep_the_ros_byte_encoding() -> None:
    placement = occupancy_grid_placement([-1, 0, 100, 50], width=2, height=2, resolution=1.0)
    assert placement.cells.dtype == np.uint8
    # -1 must survive as 255 so `Colormap.RvizMap` can draw it distinctly.
    assert 255 in placement.cells
    assert set(placement.cells.reshape(-1).tolist()) == {255, 0, 100, 50}


def test_origin_pose_is_carried_through_and_normalized() -> None:
    placement = occupancy_grid_placement(
        np.zeros(4, dtype=np.int8),
        width=2,
        height=2,
        resolution=0.25,
        origin_translation=(1.0, -2.0, 0.5),
        origin_quaternion=(0.0, 0.0, 2.0, 2.0),  # deliberately unnormalized
        frame_id="map",
    )
    np.testing.assert_allclose(placement.translation, [1.0, -2.0, 0.5])
    np.testing.assert_allclose(np.linalg.norm(placement.quaternion), 1.0)
    np.testing.assert_allclose(placement.quaternion, [0.0, 0.0, np.sqrt(0.5), np.sqrt(0.5)])
    assert placement.frame_id == "map"
    assert placement.extent == (0.5, 0.5)


def test_a_zero_quaternion_falls_back_to_identity() -> None:
    placement = occupancy_grid_placement([0], width=1, height=1, resolution=1.0, origin_quaternion=(0, 0, 0, 0))
    np.testing.assert_allclose(placement.quaternion, [0.0, 0.0, 0.0, 1.0])


def test_a_two_component_origin_is_lifted_into_3d() -> None:
    placement = occupancy_grid_placement([0], width=1, height=1, resolution=1.0, origin_translation=(3.0, 4.0))
    np.testing.assert_allclose(placement.translation, [3.0, 4.0, 0.0])


def test_mismatched_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError, match="cells"):
        occupancy_grid_placement([0, 0, 0], width=2, height=2, resolution=1.0)


def test_rgba_colorizes_free_occupied_and_unknown_distinctly() -> None:
    rgba = occupancy_to_rgba([[0, 100, -1, 50]])
    np.testing.assert_array_equal(rgba[0, 0], [255, 255, 255, 255])  # free -> white
    np.testing.assert_array_equal(rgba[0, 1], [0, 0, 0, 255])  # occupied -> black
    np.testing.assert_array_equal(rgba[0, 3], [128, 128, 128, 255])  # 50% -> mid gray
    # Unknown must not be confusable with any point on the free/occupied ramp.
    unknown = rgba[0, 2]
    assert unknown[0] != unknown[1] or unknown[1] != unknown[2]


def test_rgba_accepts_the_uint8_byte_encoding_too() -> None:
    signed = occupancy_to_rgba(np.array([[0, 100, -1]], dtype=np.int8))
    unsigned = occupancy_to_rgba(np.array([[0, 100, 255]], dtype=np.uint8))
    np.testing.assert_array_equal(signed, unsigned)


def test_unknown_can_be_made_transparent() -> None:
    rgba = occupancy_to_rgba([[-1, 0]], unknown_alpha=0)
    assert rgba[0, 0, 3] == 0
    assert rgba[0, 1, 3] == 255


def test_placement_round_trips_through_rgba_with_the_same_orientation() -> None:
    grid = np.array([[0, 0], [100, -1]], dtype=np.int8)
    placement = occupancy_grid_placement(grid.reshape(-1), width=2, height=2, resolution=1.0)
    rgba = occupancy_to_rgba(placement.cells)
    # Buffer row 0 is ROS row 1, which holds the occupied and unknown cells.
    np.testing.assert_array_equal(rgba[0, 0], [0, 0, 0, 255])
    np.testing.assert_array_equal(rgba[1, 0], [255, 255, 255, 255])
