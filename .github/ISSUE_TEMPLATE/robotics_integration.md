---
name: Robotics integration
about: ROS 2, rosbag2/MCAP, message types, frames, URDF, or a robot platform
title: ''
labels: 🤖 robotics, 👀 needs triage
assignees: ''

---

<!--
Use this template for anything about getting real robot data into Dalaran:
an unsupported message type, a bag that will not open, transforms that come out
rotated, a URDF that does not load, or a platform we should support.

Robotics-first support is the reason this fork exists, so these reports are
genuinely useful to us. See ROADMAP.md for what is already planned.
-->

## What you are integrating

<!-- e.g. "Nav2 costmaps from a Humble stack", "a Velodyne VLP-16 via
sensor_msgs/PointCloud2", "rosbag2 recorded with the mcap storage plugin". -->

## Kind of issue

- [ ] A message type is not supported, or is decoded incorrectly
- [ ] A bag or log file will not open
- [ ] Transforms / frames / axis conventions come out wrong
- [ ] URDF or robot model handling
- [ ] Live ROS 2 topics (bridge, QoS, timing)
- [ ] Something else

## ROS / middleware environment

- ROS 2 distribution: <!-- e.g. Humble, Jazzy, Rolling; or "not ROS" -->
- RMW implementation: <!-- e.g. rmw_fastrtps_cpp, rmw_cyclonedds_cpp -->
- Recording format: <!-- rosbag2 (sqlite3 / mcap), standalone MCAP, live topics -->
- Message packages and versions: <!-- e.g. nav_msgs 4.x, custom my_robot_msgs 1.2 -->

## Message definitions

<!-- If this is about a custom or uncommon message, paste the .msg / IDL
definition. We cannot decode what we cannot see the schema for. -->

```
```

## Frames and conventions

<!-- If this is about transforms: which frames are involved (map, odom,
base_link, sensor frames), which convention the data is in (REP-103 x-forward
z-up, ENU, NED, camera optical frame), and what you expected versus what you
saw. A screenshot of the wrongly-oriented result is very helpful. -->

## Sample data

<!-- A small bag, MCAP or .dlr file that reproduces this is by far the fastest
route to a fix. If you cannot share your real data, a synthetic recording that
shows the same problem works just as well. Say so if you cannot share anything —
we will work from the schema. -->

## Environment

- Dalaran version: <!-- output of `dalaran --version` -->
- SDK and version:
- OS and architecture:

## Additional context
