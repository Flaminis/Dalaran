"""
`dalaran.robot`: a high-level, opinionated logging API for robotics.

Upstream tooling gives you archetypes; this module gives you the *conventions*
that turn archetypes into a correct robot visualization:

* [`TransformTree`][dalaran.robot.TransformTree] - declare `world -> base_link -> lidar`
  once, then log transforms by name and ask tf2-style questions with
  [`TransformTree.lookup`][dalaran.robot.TransformTree.lookup].
* [`Robot`][dalaran.robot.Robot] - a handle with `log_pose`, `log_odometry`,
  `log_twist`, `log_joint_states`, `log_trajectory` and a `timestep` context
  manager that stamps a whole block of logging. Point it at a URDF with
  `Robot("arm", urdf="arm.urdf")` and joint-state messages animate the real
  link tree, mimic joints and limits included.
* Sensor helpers - [`log_lidar_scan`][dalaran.robot.log_lidar_scan],
  [`log_pointcloud`][dalaran.robot.log_pointcloud], [`log_imu`][dalaran.robot.log_imu]
  and [`log_camera`][dalaran.robot.log_camera].
* [`conventions`][dalaran.robot.conventions] - explicit REP-103 FLU vs RDF
  optical axis conversions, ENU<->NED for geographic frames, and a
  [`Rep105Chain`][dalaran.robot.conventions.Rep105Chain] that gets
  `map -> odom -> base_link` the right way round, so the most common robotics
  visualization bugs become one-liners instead of debugging sessions.

Everything uses REP-103 units and conventions: meters, radians, right-handed
frames, `x` forward / `y` left / `z` up for body frames, and quaternions in
`xyzw` order.

Examples
--------
```python
import numpy as np
import dalaran as dl

dl.init("dalaran_example_robot_api", spawn=True)

robot = dl.robot.Robot("rover")
robot.tree.add("lidar", parent="base_link")
robot.tree.set("lidar", translation=[0.2, 0.0, 0.35], static=True)

for step in range(100):
    t = step / 10.0
    with robot.timestep(t):
        robot.log_odometry(position=[t, np.sin(t), 0.0], rpy=[0.0, 0.0, np.cos(t)])
        dl.robot.log_lidar_scan(
            robot.tree.entity_path("lidar"),
            np.full(360, 5.0),
            angle_min=-np.pi,
            angle_increment=2.0 * np.pi / 360.0,
        )
```

"""

from __future__ import annotations

from . import conventions as conventions
from .conventions import (
    BASE_LINK_FRAME as BASE_LINK_FRAME,
    ENU as ENU,
    FLU as FLU,
    FRD as FRD,
    MAP_FRAME as MAP_FRAME,
    NED as NED,
    ODOM_FRAME as ODOM_FRAME,
    RDF as RDF,
    RUB as RUB,
    FrameConvention as FrameConvention,
    Rep105Chain as Rep105Chain,
    convention_matrix as convention_matrix,
    convert_frame_convention as convert_frame_convention,
    enu_to_ned as enu_to_ned,
    explain_convention as explain_convention,
    infer_convention as infer_convention,
    ned_to_enu as ned_to_enu,
)
from .frames import (
    Frame as Frame,
    TransformTree as TransformTree,
)
from .robot import (
    Joint as Joint,
    Robot as Robot,
)
from .sensors import (
    colormap_scalars as colormap_scalars,
    laser_scan_to_points as laser_scan_to_points,
    log_camera as log_camera,
    log_imu as log_imu,
    log_lidar_scan as log_lidar_scan,
    log_pointcloud as log_pointcloud,
)
from .urdf_model import (
    JointSpec as JointSpec,
    MimicSpec as MimicSpec,
    UrdfModel as UrdfModel,
)

__all__ = [
    "BASE_LINK_FRAME",
    "ENU",
    "FLU",
    "FRD",
    "MAP_FRAME",
    "NED",
    "ODOM_FRAME",
    "RDF",
    "RUB",
    "Frame",
    "FrameConvention",
    "Joint",
    "JointSpec",
    "MimicSpec",
    "Rep105Chain",
    "Robot",
    "TransformTree",
    "UrdfModel",
    "colormap_scalars",
    "convention_matrix",
    "conventions",
    "convert_frame_convention",
    "enu_to_ned",
    "explain_convention",
    "infer_convention",
    "laser_scan_to_points",
    "log_camera",
    "log_imu",
    "log_lidar_scan",
    "log_pointcloud",
    "ned_to_enu",
]
