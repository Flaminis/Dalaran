---
title: Animate a URDF robot
order: 150
description: Load a robot description once and let joint-state messages animate it
---

A `sensor_msgs/JointState` message is a list of names and numbers. Turning it
into a moving robot needs the robot description: which link each joint drives,
where the joint sits, which axis it turns about, how far it may travel, and
which joints follow other joints. `dalaran.robot.Robot` reads all of that from a
URDF, so logging a joint state is one call and no bookkeeping.

```python
import numpy as np
import dalaran as dl

dl.init("urdf_demo", spawn=True)

robot = dl.robot.Robot("arm", urdf="ur5e.urdf")

for step in range(500):
    with robot.timestep(step / 100.0):
        robot.log_joint_states(
            ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint"],
            [np.sin(step / 50.0), -0.9, 1.2],
        )
```

That is the whole program. `Robot(name, urdf=...)` is shorthand for
`Robot(name)` followed by `robot.load_urdf(...)`, which does three things:

1. logs the URDF's visual geometry;
2. declares a transform-tree frame for every link, so
   `robot.tree.lookup("base_link", "tool0")` answers the tf2 question across the
   whole model;
3. registers every non-`fixed` joint by name, so `log_joint_states` moves the
   real link tree instead of only drawing plots.

`load_urdf` accepts a path, a `dalaran.urdf.UrdfTree` you already parsed, or a [`UrdfModel`](#the-model-underneath).

## What the URDF actually controls

The joint metadata is honoured rather than approximated.

**Limits.** Values are clamped into each joint's `<limit>`, so a bad controller
setpoint bends the plot but not the robot. `continuous` joints have no limits by
definition and are never clamped; `prismatic` limits are in meters and
`revolute` limits in radians, as in the URDF.

**Axis and origin.** The joint moves about its own `<axis>`, expressed in the
joint frame placed by `<origin xyz rpy>`, using URDF's fixed-axis
`(roll, pitch, yaw)`.

**Mimic joints.** A `<mimic>` joint follows `multiplier * driver + offset`. It
never appears in a joint-state message, and it still moves:

```python
# A parallel gripper: only `left_finger` is driven, `right_finger` mimics it.
robot.log_joint_states(["left_finger"], [0.03])

# ... and the mimicking finger has moved with it.
right = robot.tree.lookup("gripper_link", "right_finger_link")
assert np.isclose(right[1, 3], -0.03)
```

Mimic chains resolve transitively, so a joint that mimics a mimicking joint also
lands in the right place. An explicit value in the message always wins over the
mimic relation, which is what you want when replaying a bag that publishes both.

## Entity paths and multiple robots

Link frames follow the same scheme as the rest of `dalaran.robot`: the entity
path is the chain of frame names under the tree root. For a URDF whose root link
is `base_link`, `gripper_link` ends up at
`world/base_link/shoulder_link/gripper_link`, and `robot.link_path("gripper_link")`
tells you so without guessing.

Two identical robots in one recording need distinct frame names, which is what
`prefix` is for. Joint *names* are never prefixed, because they have to keep
matching the incoming messages:

```python
left = dl.robot.Robot("left_arm", base_frame="left_base_link")
left.load_urdf("ur5e.urdf", prefix="left_")

right = dl.robot.Robot("right_arm", base_frame="right_base_link")
right.load_urdf("ur5e.urdf", prefix="right_")
```

## When the URDF root is not the base frame

Plenty of descriptions call their root something other than `base_link`. The
root link is then attached to the robot's base frame with an identity transform,
so both names stay addressable and `robot.log_pose(...)` still moves the entire
model:

```python
robot = dl.robot.Robot("rover", base_frame="chassis")
robot.load_urdf("rover.urdf")  # root link is "body"

robot.log_pose(translation=[3.0, 0.0, 0.0])   # moves everything
robot.link_path("body")                        # 'world/chassis/body'
```

When the root link and the base frame have the same name they are simply merged,
which is the usual case and costs nothing.

## Joint names that are not in the URDF

A typo in a joint name, or a controller that publishes a joint the description
does not have, used to be invisible. Now the value is still plotted, and the
first unknown name warns:

```text
UserWarning: Joint(s) ['gripper_joint'] are not in the URDF loaded for robot 'arm';
their values are plotted but nothing moves.
```

Only the first occurrence warns, so a 100 Hz control loop stays readable.

## The model underneath

`load_urdf` parses the description into a `UrdfModel`, available afterwards as
`robot.urdf`. It is pure Python and numpy - no viewer, no recording, no native
extension - so it is useful on its own for forward kinematics and for tests:

```python
from dalaran.robot import UrdfModel

model = UrdfModel.from_file("ur5e.urdf")
model.root_link              # 'base_link'
model.actuated_joint_names   # joints a message can drive directly
model.mimic_joint_names      # joints that follow another one

poses = model.link_transforms({"elbow_joint": 1.2})   # root_from_link, 4x4 each
values = model.resolve_positions({"left_finger": 0.03})  # mimics expanded, limits applied
```

`UrdfModel.from_urdf_tree(tree)` adopts a description that
`dalaran.urdf.UrdfTree` already parsed, so the
file is only read once when you want both the geometry and the math.
