<!--[metadata]
title = "Robot arm teleop"
description = "A mobile manipulator driving a figure-eight while its arm, lidar, IMU and camera are logged through the high-level `dalaran.robot` API."
tags = ["3D", "robotics", "transforms", "lidar", "API example"]
-->

A mobile manipulator drives a figure-eight around a square room while a
three-joint arm sweeps above it. The base pose, the arm joints, a 2D laser scan,
an IMU and a pinhole camera are all logged through [`dalaran.robot`][], the
high-level robotics API.

## Why this example exists

Written against the raw archetype API, this scene needs you to hand-roll a
transform tree, compose forward kinematics for every joint, project the laser
scan yourself and remember that the camera lives in an optical frame. The
`dalaran.robot` layer does all four, so this file is mostly *simulation* code
with a thin logging layer on top.

## Used Dalaran types

[`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d),
[`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d),
[`Arrows3D`](https://www.dalaran.dev/docs/reference/types/archetypes/arrows3d),
[`LineStrips3D`](https://www.dalaran.dev/docs/reference/types/archetypes/linestrips3d),
[`Scalars`](https://www.dalaran.dev/docs/reference/types/archetypes/scalars),
[`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole),
[`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image),
[`Boxes3D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes3d)

## Logging and visualizing with Dalaran

The robot's frames and joints are declared once, before the loop starts. Entity
paths follow the frame hierarchy automatically, so `lidar` ends up at
`world/base_link/lidar`:

```python
robot = dl.robot.Robot("mobile_manipulator", base_frame="base_link")

robot.tree.add("lidar", parent="base_link")
robot.tree.set("lidar", translation=[0.15, 0.0, 0.35], static=True)

robot.add_joint("shoulder_pan", parent="base_link", origin=[0.0, 0.0, 0.35], axis=[0, 0, 1])
robot.add_joint("shoulder_lift", parent="shoulder_pan", origin=[0.0, 0.0, 0.1], axis=[0, 1, 0])
robot.add_joint("elbow", parent="shoulder_lift", origin=[0.0, 0.0, 0.45], axis=[0, 1, 0])
```

The camera is mounted with the REP-103 optical rotation, expressed explicitly
rather than as a magic quaternion:

```python
robot.tree.set(
    "camera",
    translation=[0.25, 0.0, 0.3],
    rotation_matrix=dl.robot.convention_matrix(dl.robot.FLU, dl.robot.RDF).T,
    static=True,
)
```

Each simulation step sets the timeline once and then logs odometry, joints and
sensors. `log_odometry` moves the base frame, draws the body twist as arrows and
extends the travelled path:

```python
with robot.timestep(t):
    robot.log_odometry(
        position=position,
        rpy=[0.0, 0.0, heading],
        linear_velocity=[1.0, 0.0, 0.0],
        angular_velocity=[0.0, 0.0, float(np.cos(t))],
    )
    robot.log_joint_states(["shoulder_pan", "shoulder_lift", "elbow"], joints)

    dl.robot.log_lidar_scan(
        robot.tree.entity_path("lidar"),
        ranges,  # `inf` beams are dropped for you
        angle_min=-np.pi,
        angle_increment=2.0 * np.pi / 360,
        colorize_by_range=True,
    )
```

Finally, the tf2 question everybody asks - where is the gripper in the world? -
is a single call:

```python
world_from_gripper = robot.tree.lookup("world", "gripper")
print(world_from_gripper[:3, 3])
```

## Run the code

To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/robot_arm_teleop
```
To experiment with the provided example, simply execute the main Python script:
```bash
python examples/python/robot_arm_teleop/main.py
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python examples/python/robot_arm_teleop/main.py --help
```
