<!--[metadata]
title = "ROS 2 TurtleBot"
description = "Stream a TurtleBot's ROS 2 topics into Dalaran live or from a rosbag2 recording, including a custom message converter."
tags = ["ROS", "robotics", "2D", "3D", "API example"]
-->

Visualize a TurtleBot's ROS 2 topics with Dalaran: the transform tree, the laser
scan, the occupancy map, odometry, the IMU, and a battery topic that Dalaran
does not know about out of the box.

## Running it

The example has three modes.

```sh
# No ROS required: synthesize the messages a TurtleBot publishes and push them
# through the very same converters. Good for seeing what you will get.
python ros2_turtlebot.py simulate

# Subscribe to a live ROS 2 graph, e.g. a real TurtleBot 4 or a Gazebo simulation.
python ros2_turtlebot.py live

# Replay a rosbag2 recording.
python ros2_turtlebot.py bag path/to/my_bag
```

The `live` and `bag` modes need a sourced ROS 2 installation; `simulate` does
not, because `dalaran.ros2` imports `rclpy` lazily.

## What it shows

* **The transform tree.** `/tf` and `/tf_static` drive a
  [`dalaran.robot.TransformTree`][], so `world -> odom -> base_footprint ->
  base_scan` becomes an entity hierarchy and every sensor reading is placed in
  the frame it was measured in.
* **The laser scan.** `sensor_msgs/LaserScan` is projected with the REP-103
  angle convention, with `inf` "no return" beams dropped.
* **The map.** `nav_msgs/OccupancyGrid` becomes a native
  [`dalaran.GridMap`][], correctly oriented and placed by its `info.origin`
  pose, with unobserved cells rendered distinctly from free space.
* **Odometry and IMU** as poses, arrows and per-axis time series.
* **A custom message type.** `sensor_msgs/BatteryState` is not built in, and the
  example registers it in eight lines:

  ```python
  from dalaran.ros2 import register

  @register("sensor_msgs/msg/BatteryState")
  def log_battery_state(msg, entity_path, ctx):
      ctx.log(f"{entity_path}/percentage", dl.Scalars(float(msg.percentage)))
      ctx.log(f"{entity_path}/voltage", dl.Scalars(float(msg.voltage)))
      ctx.log(f"{entity_path}/current", dl.Scalars(float(msg.current)))
  ```

  Once registered, the type works everywhere: live bridging, bag replay and the
  `dalaran-ros2` command line tool.

## Doing the same thing without writing any code

```sh
dalaran-ros2 bridge --allow '/tf' --allow '/tf_static' --allow '/scan' \
                    --allow '/odom' --allow '/map' --max-hz '/oakd/*=5'
```

## Used Dalaran types

[`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d),
[`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d),
[`GridMap`](https://www.dalaran.dev/docs/reference/types/archetypes/grid_map),
[`Arrows3D`](https://www.dalaran.dev/docs/reference/types/archetypes/arrows3d),
[`Scalars`](https://www.dalaran.dev/docs/reference/types/archetypes/scalars)
