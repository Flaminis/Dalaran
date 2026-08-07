---
title: Log a robot with the high-level robot API
order: 100
description: Transform trees, joints, odometry and sensor conventions with `dalaran.robot`
---

`dalaran.robot` is a Python layer on top of the core SDK that knows how robots
are put together. Instead of hand-rolling a transform tree, forward kinematics
and sensor projections for every project, you declare the robot once and log
against it.

Everything in this API uses [REP-103](https://www.ros.org/reps/rep-0103.html)
units and conventions: meters, radians, right-handed frames, `x` forward /
`y` left / `z` up for body frames, and quaternions in `xyzw` order.

```python
import numpy as np
import dalaran as dl

dl.init("robot_demo", spawn=True)

robot = dl.robot.Robot("rover")
robot.tree.add("lidar", parent="base_link")
robot.tree.set("lidar", translation=[0.2, 0.0, 0.35], static=True)

for step in range(200):
    t = step / 20.0
    with robot.timestep(t):
        robot.log_odometry(
            position=[np.cos(t), np.sin(t), 0.0],
            rpy=[0.0, 0.0, t + np.pi / 2],
            linear_velocity=[1.0, 0.0, 0.0],
            angular_velocity=[0.0, 0.0, 1.0],
        )
```

## Transform trees

A `TransformTree` maps
named coordinate frames onto Dalaran entity paths. Declaring
`world -> base_link -> lidar` gives the entity path `world/base_link/lidar`, and
`tree.set("lidar", ...)` logs a `Transform3D` on exactly that entity.

```python
tree = dl.robot.TransformTree(root="world")
tree.add_chain("base_link", "arm", "gripper")

tree.set("base_link", translation=[1.0, 0.0, 0.0], rpy=[0.0, 0.0, np.pi / 2])
tree.set("arm", translation=[0.0, 0.0, 0.4])
tree.set("gripper", quaternion=[0.0, 0.0, 0.0, 1.0])
```

Rotations may be given in whichever form your data already has - a quaternion in
`xyzw` order, a 3x3 rotation matrix, fixed-axis `(roll, pitch, yaw)` angles, or a
full 4x4 homogeneous matrix:

| Argument          | Shape    | Notes                                       |
| ----------------- | -------- | ------------------------------------------- |
| `quaternion`      | `(4,)`   | `(x, y, z, w)`, as in ROS and Eigen         |
| `rotation_matrix` | `(3, 3)` | Must be orthonormal and right-handed        |
| `rpy`             | `(3,)`   | Fixed-axis roll/pitch/yaw, as in URDF       |
| `matrix`          | `(4, 4)` | Supplies rotation *and* translation         |

Transforms follow the same convention as `Transform3D` and as ROS: the transform
stored for a frame is `parent_from_child`, so it maps points expressed in the
child frame into the parent frame.

### `lookup`, the tf2 question

The one thing people miss most when moving from ROS is
`tf2::lookup_transform`. `TransformTree.lookup(target, source)` is exactly that:

```python
# Where is the gripper, in world coordinates?
world_from_gripper = tree.lookup("world", "gripper")
print(world_from_gripper[:3, 3])

# And where is the world origin, seen from the gripper?
gripper_from_world = tree.lookup("gripper", "world")
```

The result is a plain 4x4 numpy matrix, so it composes with the rest of your
math and can be fed straight back into `tree.set(..., matrix=...)`. There is also
`tree.transform_points(points, source, target)` for moving `(N, 3)` point arrays
between frames.

## Robots and joints

`Robot` owns a transform
tree, a timeline and the odometry trail.

```python
robot = dl.robot.Robot("arm", base_frame="base_link")

robot.add_joint("shoulder", parent="base_link", origin=[0.0, 0.0, 0.2], axis=[0, 0, 1])
robot.add_joint("elbow", parent="shoulder", origin=[0.0, 0.0, 0.4], axis=[0, 1, 0])

for step in range(200):
    with robot.timestep(step):
        robot.log_joint_states(
            ["shoulder", "elbow"],
            [np.sin(step / 20.0), -np.cos(step / 20.0)],
        )
```

Because the joints were declared against the tree, `log_joint_states` both plots
the joint positions as scalar time series *and* animates the transform tree. If
you only want the plots, pass `animate=False`.

`Robot.timestep` infers the kind of time from its argument: an `int` becomes a
sequence index, a `float` or `timedelta` a duration in seconds, and a `datetime`
an absolute timestamp. Setting the timeline once per block is much harder to get
wrong than sprinkling `set_time` calls through a logging function.

Other methods:

* `log_pose(...)` moves the base frame (or any other frame via `frame=`).
* `log_twist(linear=..., angular=...)` draws a `geometry_msgs/Twist` as body-frame arrows.
* `log_trajectory(points)` draws a path as a single line strip.
* `log_odometry(...)` does all three at once and accumulates the travelled path.

## Sensors

The sensor helpers encode the convention that goes with each sensor.

```python
# A sensor_msgs/LaserScan. `inf` and `nan` beams and out-of-range returns are
# dropped, so you do not get a spray of garbage points at the origin.
dl.robot.log_lidar_scan(
    robot.tree.entity_path("lidar"),
    ranges,
    angle_min=-np.pi,
    angle_increment=2.0 * np.pi / 360,
    range_max=25.0,
    colorize_by_range=True,
)

# A point cloud, colormapped by any per-point scalar.
dl.robot.log_pointcloud("world/base_link/lidar", xyz, intensity=xyz[:, 2])

# An IMU, logged both as arrows and as per-axis scalars: a sign error is
# invisible in a plot but obvious as an arrow.
dl.robot.log_imu(
    "world/base_link/imu",
    linear_acceleration=[0.0, 0.0, 9.81],
    angular_velocity=[0.0, 0.0, 0.2],
)

# A pinhole camera, from fx/fy/cx/cy or from a full K matrix.
dl.robot.log_camera(
    "world/base_link/camera",
    width=640,
    height=480,
    fx=525.0,
    image=rgb,
)
```

If you already have cartesian scan points and just want the projection math,
`dl.robot.laser_scan_to_points(...)` returns the `(N, 3)` array without logging
anything.

## Axis conventions

Mixing up axis conventions is the single most common robotics visualization
bug. `dalaran.robot` makes them explicit. A convention is a three-letter code
saying what the local `+X`, `+Y` and `+Z` axes point at, using
`F`orward / `B`ack / `L`eft / `R`ight / `U`p / `D`own:

| Convention | Meaning                          | Where you meet it                        |
| ---------- | -------------------------------- | ---------------------------------------- |
| `FLU`      | x forward, y left, z up          | REP-103 body and world frames            |
| `RDF`      | x right, y down, z forward       | REP-103 optical frames, OpenCV, every `K` |
| `FRD`      | x forward, y right, z down       | Aerospace body frames, PX4, ArduPilot    |
| `RUB`      | x right, y up, z back            | OpenGL and glTF cameras                  |

```python
from dalaran.robot import FLU, RDF, convention_matrix, convert_frame_convention

# Re-express points measured in an FLU body frame in the camera's optical frame.
points_rdf = convert_frame_convention(points_flu, FLU, RDF)

# Or grab the rotation itself, for example to mount a camera on an FLU robot:
robot.tree.set(
    "camera",
    translation=[0.25, 0.0, 0.3],
    rotation_matrix=convention_matrix(FLU, RDF).T,
    static=True,
)
```

`convert_frame_convention` also accepts a 4x4 transform, which it converts by
the similarity `R @ T @ R.T` so the result describes the same physical transform
written in the destination convention. Left-handed or degenerate codes such as
`"FLD"` or `"FLB"` are rejected instead of silently mirroring your scene.

## A complete example

The [robot arm teleop example](https://github.com/Flaminis/Dalaran/tree/main/examples/python/robot_arm_teleop)
puts all of this together: a mobile manipulator driving a figure-eight with an
animated three-joint arm, a simulated laser scan, an IMU and a camera.
