"""Tests for routing nav2 costmap topics and messages to the costmap converters."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from dalaran.ros2 import msg_map
from dalaran.ros2.costmap import RVIZ_COST_PALETTE

from .fake_msgs import Simple, header, pose, vec3


def occupancy_costmap(values: list[int]) -> Simple:
    """A nav2 costmap published as a `nav_msgs/OccupancyGrid`, i.e. on the 0..100 scale."""
    return Simple(
        header=header(frame_id="map"),
        info=Simple(width=2, height=2, resolution=0.05, origin=pose(vec3(-1.0, -2.0, 0.0))),
        data=values,
    )


def nav2_costmap(values: list[int]) -> Simple:
    """A `nav2_msgs/Costmap`, i.e. raw 0..255 cost with geometry in `metadata`."""
    return Simple(
        header=header(frame_id="odom"),
        metadata=Simple(
            size_x=2,
            size_y=2,
            resolution=0.1,
            layer="inflation",
            origin=pose(vec3(1.0, 2.0, 0.0)),
        ),
        data=values,
    )


def test_costmap_topics_route_to_the_costmap_converter() -> None:
    for topic in (
        "/global_costmap/costmap",
        "/local_costmap/costmap",
        "/robot1/local_costmap/costmap",
        "/keepout_costmap/costmap",
    ):
        assert msg_map.lookup_topic(topic) is msg_map.convert_costmap_occupancy_grid, topic


def test_a_plain_map_topic_still_uses_the_occupancy_grid_converter() -> None:
    assert msg_map.lookup_topic("/map") is None
    assert msg_map.lookup("nav_msgs/OccupancyGrid") is msg_map.convert_occupancy_grid


def test_the_nav2_costmap_message_type_is_registered() -> None:
    assert msg_map.lookup("nav2_msgs/Costmap") is msg_map.convert_costmap
    assert "nav2_msgs/msg/Costmap" in msg_map.registered_types()


def test_convert_prefers_the_topic_over_the_type(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    grid = occupancy_costmap([0, 100, 99, -1])
    assert msg_map.convert("nav_msgs/OccupancyGrid", grid, "map/local_costmap", ctx, topic="/local_costmap/costmap")
    grid_map = captured.first("GridMap")
    # The costmap converter logs RGBA layers; the plain map converter logs an
    # L-channel buffer with a colormap.
    assert grid_map.kwargs["format"].kwargs["color_model"] == "RGBA"
    assert captured.paths == ["map/local_costmap/costmap"]


def test_without_a_topic_the_type_still_decides(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    assert msg_map.convert("nav_msgs/OccupancyGrid", occupancy_costmap([0, 100, 99, -1]), "map", ctx)
    assert captured.first("GridMap").kwargs["colormap"] == "Colormap.RvizMap"


def test_a_squeezed_costmap_keeps_its_obstacle_categories(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    # 99 is INSCRIBED_INFLATED_OBSTACLE and 100 is LETHAL_OBSTACLE on this scale;
    # neither is "almost fully occupied".
    msg_map.convert_costmap_occupancy_grid(occupancy_costmap([0, 50, 99, 100]), "map/global_costmap", ctx)
    grid_map = captured.first("GridMap")
    rgba = np.frombuffer(grid_map.kwargs["data"], dtype=np.uint8).reshape(2, 2, 4)
    # Buffer row 0 is the message's last row, which holds 99 and 100.
    np.testing.assert_array_equal(rgba[0, 0, :3], RVIZ_COST_PALETTE.inscribed)
    np.testing.assert_array_equal(rgba[0, 1, :3], RVIZ_COST_PALETTE.lethal)
    assert rgba[1, 0, 3] == 0  # free space stays see-through


def test_a_nav2_costmap_message_uses_its_metadata_geometry(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    msg_map.convert_costmap(nav2_costmap([0, 128, 253, 254]), "odom/local_costmap", ctx)
    grid_map = captured.first("GridMap")
    assert grid_map.kwargs["cell_size"] == pytest.approx(0.1)
    np.testing.assert_allclose(grid_map.kwargs["translation"], [1.0, 2.0, 0.0])
    # The metadata's layer name becomes the entity, so several layers of one
    # costmap stack instead of overwriting each other.
    assert captured.paths == ["odom/local_costmap/inflation"]


def test_raw_reserved_costs_are_drawn_distinctly(_fake_dl: Any, ctx: Any, captured: Any) -> None:
    msg_map.convert_costmap(nav2_costmap([0, 128, 253, 254]), "odom/local_costmap", ctx)
    rgba = np.frombuffer(captured.first("GridMap").kwargs["data"], dtype=np.uint8).reshape(2, 2, 4)
    np.testing.assert_array_equal(rgba[0, 0, :3], RVIZ_COST_PALETTE.inscribed)
    np.testing.assert_array_equal(rgba[0, 1, :3], RVIZ_COST_PALETTE.lethal)
    assert tuple(rgba[1, 1, :3]) not in {RVIZ_COST_PALETTE.inscribed, RVIZ_COST_PALETTE.lethal}
