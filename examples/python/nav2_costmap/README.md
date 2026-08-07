<!--[metadata]
title = "nav2 costmaps"
tags = ["2D", "3D", "ROS", "Robotics", "Navigation"]
-->

A synthetic nav2 navigation stack: a layered global costmap - static, obstacle
and the two inflation layers computed from them - plus a rolling local costmap
window that follows the robot along its plan.

The point of the example is the costmap semantics. `253`
(`INSCRIBED_INFLATED_OBSTACLE`) and `254` (`LETHAL_OBSTACLE`) are drawn in their
own colors rather than at the top of the cost gradient, so an inflation ring can
never be mistaken for a merely expensive cell, and `255` (`NO_INFORMATION`) is
transparent, so the parts of the local window that have left the map show the
global costmap underneath instead of blanking it out.

Run it from a checkout of the repository:

```bash
python examples/python/nav2_costmap/nav2_costmap.py
```

See [Visualize nav2 costmaps](https://dalaran.dev/docs/howto/robotics/costmaps)
for the API this example uses.
