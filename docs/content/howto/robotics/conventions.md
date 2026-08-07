---
title: Get the frame conventions right
order: 160
description: REP-103 axis bases, ENU/NED geographic frames and the REP-105 map/odom/base_link chain
---

Most "the point cloud is rotated" and "the robot teleports" bugs are not maths
bugs. They are convention bugs: an optical frame treated as a body frame, a NED
heading fed to an ENU visualizer, or `map -> base_link` published directly.
`dalaran.robot.conventions` makes each of those explicit enough to assert on.

## Body axes: FLU, RDF, FRD, RUB

A convention is a three-letter code saying what the local `+X`, `+Y` and `+Z`
axes point at, using `F`orward / `B`ack / `L`eft / `R`ight / `U`p / `D`own:

| Convention | Meaning                    | Where you meet it                         |
| ---------- | -------------------------- | ----------------------------------------- |
| `FLU`      | x forward, y left, z up    | REP-103 body and world frames             |
| `RDF`      | x right, y down, z forward | REP-103 optical frames, OpenCV, every `K` |
| `FRD`      | x forward, y right, z down | Aerospace body frames, PX4, ArduPilot     |
| `RUB`      | x right, y up, z back      | OpenGL and glTF cameras                   |

```python
from dalaran.robot import FLU, RDF, convention_matrix, convert_frame_convention

points_rdf = convert_frame_convention(points_flu, FLU, RDF)
```

See [the robot API guide](robot-api.md#axis-conventions) for more on those two
functions. The rest of this page is about the conventions that are not just an
axis permutation.

## Frame names carry a convention

REP-103 states one naming rule, and it is the one that matters: a frame whose
name ends in `_optical_frame` is `RDF`, everything else is `FLU`.
`infer_convention` applies it, and `explain_convention` also hands back its
reasoning, which is worth printing next to a suspicious sensor:

```python
from dalaran.robot import conventions

conventions.infer_convention("camera_color_optical_frame")  # 'RDF'
conventions.infer_convention("velodyne")                     # 'FLU'

why = conventions.explain_convention("camera_color_optical_frame")
print(why)
# camera_color_optical_frame: RDF (the name ends in '_optical_frame', which
# REP-103 reserves for optical frames: x right, y down, z forward ...)

# The explanation carries the rotation, so you can act on it directly:
ray_flu = why.matrix_to(conventions.FLU) @ [0.0, 0.0, 1.0]   # [1, 0, 0]
```

Entity-path-style names (`world/base_link/camera_optical_frame`) are understood,
so this works on a `TransformTree` entity path as well as on a bare frame id.

Named constants are provided for the standard frames -
`MAP_FRAME`, `ODOM_FRAME`, `BASE_LINK_FRAME`, `BASE_FOOTPRINT_FRAME`,
`EARTH_FRAME` - and for the optical suffixes, `OPTICAL_FRAME_SUFFIXES`.

## Geographic frames: ENU and NED

ROS works in east-north-up. Autopilots, INS units and most geodetic software
work in north-east-down. Converting a *position* between them is a swap and a
sign flip; converting an *orientation* is where hand-rolled code loses an axis,
because the body frame changes from `FLU` to `FRD` at the same time.

```python
import numpy as np
from dalaran.robot import conventions

# Positions and vectors, any shape ending in 3.
conventions.enu_to_ned([10.0, 0.0, 2.0])        # [0., 10., -2.]
conventions.ned_to_enu(gnss_velocity_ned)

# Orientations, as quaternions (xyzw) or as 3x3 matrices.
q_ned = conventions.enu_to_ned_quaternion(imu_msg_orientation_xyzw)
r_enu = conventions.ned_to_enu_rotation_matrix(r_ned)

# Whole poses.
pose_ned = conventions.enu_to_ned(pose_enu)     # (4, 4) in, (4, 4) out
```

The mental check: an `FLU` robot with identity orientation in ENU is facing
**east**, and east is a heading of 90 degrees in NED. So

```python
np.arctan2(*conventions.enu_to_ned_rotation_matrix(np.eye(3))[[1, 0], 0]) == np.pi / 2
```

More generally `yaw_ned = pi/2 - yaw_enu`, pitch changes sign with the flipped
body `y` axis, and roll does not.

Pass `body=False` when the child frame is itself axis-aligned with the world -
a map tile, a wind field, anything that is not a vehicle - and only the world
axes are re-expressed.

The conversion is an involution: `enu_ned_matrix()` is its own inverse, which is
why `enu_to_ned` and `ned_to_enu` share an implementation and why round-tripping
is exact rather than nearly exact.

## REP-105: map, odom and base_link

[REP-105](https://www.ros.org/reps/rep-0105.html) splits the robot's pose into
two transforms produced by two different nodes:

| Transform          | Published by                                    | Character                                |
| ------------------ | ----------------------------------------------- | ---------------------------------------- |
| `map -> odom`      | localization: AMCL, a SLAM backend, a GPS fuser | jumps whenever the estimate is corrected |
| `odom -> base_link`| odometry: wheel encoders, VIO, an EKF           | smooth and continuous, but drifts        |

Publishing `map -> base_link` directly is the classic mistake. It makes the
`odom` frame meaningless, and anything that relies on a continuous frame - local
planners, point cloud accumulation, motion filters - starts to twitch every time
localization corrects itself.

`Rep105Chain` names its setters after the node that owns the transform, so the
correct thing is also the obvious thing:

```python
import dalaran as dl
from dalaran.robot.conventions import Rep105Chain

dl.init("rep105_demo", spawn=True)
chain = Rep105Chain()          # declares map -> odom -> base_link

# In the odometry callback:
chain.set_odometry(translation=[x, y, 0.0], quaternion=q)

# In the localization callback:
chain.set_localization(translation=[dx, dy, 0.0], rpy=[0.0, 0.0, dtheta])

# Reading the robot's pose is a question, not a publication:
chain.pose_in_map()               # map_from_base, composed from the chain
chain.pose_in_odom()              # odom_from_base, the smooth one
chain.localization_correction()   # map_from_odom, the drift absorbed so far
```

### "But I only have the pose in the map"

That is what a global localization system actually estimates, and it is exactly
the situation that tempts people to publish `map -> base_link`.
`set_pose_in_map` does the right thing instead: it derives the `map -> odom`
correction that makes the existing odometry agree with the estimate,
`map_from_odom = map_from_base @ odom_from_base^-1`, and publishes that.

```python
from dalaran.robot._math import make_matrix

chain.set_odometry(translation=[10.0, 0.0, 0.0])          # odometry says 10.0 m
chain.set_pose_in_map(make_matrix(translation=[10.5, 0.0, 0.0]))  # GPS says 10.5 m

chain.pose_in_map()[:3, 3]    # [10.5, 0, 0] - the estimate is honoured
chain.pose_in_odom()[:3, 3]   # [10. , 0, 0] - the odometry is untouched
```

### Sensors on the chain

`attach` declares a sensor frame under `base_link` and returns the convention its
name implies, so mounting a camera and knowing it is `RDF` is one call:

```python
chain.attach("camera_color_optical_frame")   # 'RDF'
chain.attach("velodyne")                     # 'FLU'
```

`Rep105Chain` wraps an ordinary [`TransformTree`](robot-api.md#transform-trees),
available as `chain.tree`, so `lookup`, `transform_points` and everything else
keep working. Pass an existing tree to `Rep105Chain(tree)` to add the chain to a
recording you have already laid out; the tree must be rooted at the map frame,
because in REP-105 nothing above `map` is the robot's business.
