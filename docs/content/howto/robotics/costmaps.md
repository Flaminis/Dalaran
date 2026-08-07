---
title: Visualize nav2 costmaps
order: 300
description: Cost semantics, layered costmaps and the rolling local window with `dalaran.ros2.costmap`
---

A ROS costmap is not an occupancy grid with a different name, and treating it as
one is how a navigation debugging session goes wrong. `dalaran.ros2.costmap`
models nav2's cost semantics directly, stacks a costmap's layers as separate grid
maps, and handles the local costmap's sliding window.

## Cost values are categories, not a gradient

`nav2_costmap_2d` stores a cost per cell:

| value | meaning |
| --- | --- |
| `0` | free space |
| `1..=252` | increasing cost, usually the inflation layer's decay curve |
| `253` | `INSCRIBED_INFLATED_OBSTACLE`: the robot's inscribed circle would collide |
| `254` | `LETHAL_OBSTACLE`: an observed obstacle |
| `255` | `NO_INFORMATION`: never observed (spelled `-1` on `OccupancyGrid` topics) |

The top three values are *categories*. If they are drawn somewhere on the cost
gradient, an inflated-obstacle ring ends up looking like "cost 200" and you can no
longer tell whether the planner refused a cell because the robot would collide
there or merely because it was expensive. Every palette here gives those three
values their own hue, off the gradient:

```python
import numpy as np
from dalaran.ros2.costmap import costmap_to_rgba

rgba = costmap_to_rgba([0, 128, 253, 254, 255])
assert rgba[0, 3] == 0  # free space is transparent
assert rgba[4, 3] == 0  # so is never-observed space
np.testing.assert_array_equal(rgba[2][:3], [0, 255, 255])  # inscribed: cyan
np.testing.assert_array_equal(rgba[3][:3], [255, 0, 255])  # lethal: magenta
```

Pass `palette=DALARAN_COST_PALETTE` for the same semantics in the Dalaran palette,
matching the viewer's built-in [`Colormap.Costmap`](../../reference/types/components/colormap.md).

### nav2 publishes cost in two different scales

`nav2_msgs/msg/Costmap` carries the raw `0..=255` value. The far more common
`/global_costmap/costmap` and `/local_costmap/costmap` topics are plain
`nav_msgs/OccupancyGrid` messages whose values have been squeezed through
`costmap_2d`'s translation table into `0..=100`, where `99` is
`INSCRIBED_INFLATED_OBSTACLE` and `100` is `LETHAL_OBSTACLE`. Both directions of
that translation are available, and `costmap_to_rgba` takes a `scale` argument so
one palette covers both:

```python
from dalaran.ros2.costmap import occupancy_byte_to_raw_cost, raw_cost_to_occupancy_byte

assert list(raw_cost_to_occupancy_byte([0, 1, 252, 253, 254, 255])) == [0, 1, 98, 99, 100, 255]
assert list(occupancy_byte_to_raw_cost([99, 100, -1])) == [253, 254, 255]

rgba = costmap_to_rgba([0, 50, 99, 100], scale="occupancy")
```

Because the *type* of a costmap topic says "occupancy probability" while its
payload says "cost", the bridge routes these topics by name. `register_topic`
adds a topic-glob table that `convert` consults before the type table, so
`/global_costmap/costmap`, `/local_costmap/costmap`, `/robot1/local_costmap/costmap`
and `nav2_msgs/msg/Costmap` all reach the costmap converters automatically while
`/map` keeps using the plain occupancy-grid converter.

## Layered costmaps

nav2 composes each costmap out of plugins - `static_layer`, `obstacle_layer`,
`voxel_layer`, `inflation_layer` - and when a robot refuses to move you need to
know which layer put the cost there. Log them as a stack:

```python
import dalaran as dl
from dalaran.ros2.costmap import CostmapLayer, log_costmap_layers
from dalaran.ros2.occupancy_grid import occupancy_grid_placement

placement = occupancy_grid_placement(
    grid.data,
    width=grid.info.width,
    height=grid.info.height,
    resolution=grid.info.resolution,
    origin_translation=(grid.info.origin.position.x, grid.info.origin.position.y, 0.0),
)

log_costmap_layers(
    "map/global_costmap",
    [
        CostmapLayer("static", static_cells),
        CostmapLayer("obstacle", obstacle_cells),
        CostmapLayer("inflation", inflation_cells),
    ],
    placement,
)
```

Every layer shares one placement, so they stay aligned by construction. Each gets

* its own entity path, so a layer can be toggled or styled on its own,
* an increasing `draw_order`, so the viewer stacks them in plugin order no matter
  what order the chunks arrive in, and
* an `opacity`: the bottom layer stays opaque and everything above it is
  translucent, so you can see the static map through the inflation layer.

Layers are logged as RGBA rather than as a single channel plus a colormap, which
is what makes free and `NO_INFORMATION` cells fully transparent. That is the whole
point of layering: an unobserved cell in the obstacle layer must show the static
map underneath rather than paint over it. Use
`plan_costmap_layers` if you only want the resolved paths, draw orders and
opacities without logging anything.

## The local costmap is a rolling window

`/local_costmap/costmap` is a small grid that slides with the robot, so its
`info.origin` is different in nearly every message while the grid keeps its size.
Two things go wrong here:

* **Do not log it as static data.** Static pins the pose to the first origin while
  the contents keep updating, so obstacles appear in the wrong place.
* **Do not put the origin in the entity path.** That creates thousands of
  one-frame entities that are never cleared.

The local costmap is *one entity that moves*. `RollingCostmapWindow` enforces
that, and reports how far the window travelled so a resampled or smeared window is
easy to spot:

```python
from dalaran.ros2.costmap import CostmapLayer, RollingCostmapWindow

window = RollingCostmapWindow("odom/local_costmap")

for msg in local_costmap_messages:
    placement = occupancy_grid_placement(
        msg.data,
        width=msg.info.width,
        height=msg.info.height,
        resolution=msg.info.resolution,
        origin_translation=(msg.info.origin.position.x, msg.info.origin.position.y, 0.0),
    )
    shift = window.log([CostmapLayer("costmap", msg.data, scale="occupancy")], placement)
    if shift.resized:
        print("the local costmap was reconfigured mid-run")
```

If you build a window yourself rather than replaying nav2's, `rolling_window_origin`
reproduces nav2's origin math, including the snap to whole cells that keeps the
grid from being resampled on every update:

```python
from dalaran.ros2.costmap import rolling_window_origin

origin = rolling_window_origin(robot_xy, width=60, height=60, resolution=0.05)
```

## A runnable example

`examples/python/nav2_costmap` builds a small synthetic nav2 stack - a static map,
an obstacle layer, an inflation layer and a rolling local window following a robot
along a path - and logs it exactly the way the ROS 2 bridge would:

```sh
python examples/python/nav2_costmap/nav2_costmap.py
```

## Related

* [Visualize ROS 2 data](ros2.md) - the bridge, the converter registry and `/tf`.
* [`GridMap`](../../reference/types/archetypes/grid_map.md) - the archetype every
  costmap layer is logged as.
