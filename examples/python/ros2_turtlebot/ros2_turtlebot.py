#!/usr/bin/env python3
"""
Visualize a TurtleBot's ROS 2 topics with Dalaran.

Run it against a live robot (or a Gazebo simulation):

    python -m ros2_turtlebot live

Or against a rosbag2 recording:

    python -m ros2_turtlebot bag path/to/my_bag

With `--simulate` it needs no ROS at all: it synthesizes the same message types
a TurtleBot publishes and pushes them through the very same converters, which is
a convenient way to see what the visualization will look like before you have a
robot in front of you.
"""

from __future__ import annotations

import argparse
import math

import numpy as np

import dalaran as dl  # pip install dalaran-sdk
import dalaran.blueprint as dlb
from dalaran.ros2 import Ros2Bridge, register

# The topics a TurtleBot 4 / Nav2 stack publishes that are worth seeing.
TOPICS = [
    "/tf",
    "/tf_static",
    "/scan",
    "/odom",
    "/map",
    "/global_costmap/costmap",
    "/plan",
    "/imu",
    "/joint_states",
    "/battery_state",
    "/oakd/rgb/preview/image_raw",
]

# The camera is the only topic that can genuinely swamp the recording.
RATE_LIMITS = {"/oakd/*": 5.0, "/imu": 50.0}


@register("sensor_msgs/msg/BatteryState")
def log_battery_state(msg, entity_path: str, ctx) -> None:
    """
    Log a battery as three scalar series.

    `sensor_msgs/BatteryState` is not one of Dalaran's built-in conversions, and
    it does not need to be: this is the whole of what it takes to teach the
    bridge about a new message type. The decorated function is picked up by the
    live bridge, the bag replayer and the `dalaran-ros2` CLI alike.
    """
    ctx.log(f"{entity_path}/percentage", dl.Scalars(float(msg.percentage)))
    ctx.log(f"{entity_path}/voltage", dl.Scalars(float(msg.voltage)))
    ctx.log(f"{entity_path}/current", dl.Scalars(float(msg.current)))


def blueprint() -> dlb.BlueprintLike:
    """A layout that puts the map next to the camera, with the time series below."""
    return dlb.Blueprint(
        dlb.Horizontal(
            dlb.Spatial3DView(origin="/", name="World"),
            dlb.Vertical(
                dlb.Spatial2DView(origin="/oakd/rgb/preview/image_raw", name="Camera"),
                dlb.TimeSeriesView(origin="/battery_state", name="Battery"),
                dlb.TimeSeriesView(origin="/imu", name="IMU"),
            ),
            column_shares=[2, 1],
        ),
        collapse_panels=True,
    )


def make_bridge() -> Ros2Bridge:
    """Build the bridge both the live and the bag mode use."""
    return Ros2Bridge(
        allow=TOPICS,
        max_hz=RATE_LIMITS,
        # Put the scan on the lidar's own frame so it moves with the robot even
        # before /tf has told us where `base_scan` lives.
        topic_paths={"/scan": "world/odom/base_footprint/base_scan"},
    )


def run_live(duration: float | None) -> None:
    """Subscribe to a running ROS 2 graph."""
    with make_bridge() as bridge:
        bridge.spin(duration=duration)


def run_bag(path: str, speed: float) -> None:
    """Replay a rosbag2 recording."""
    from dalaran.ros2.bag import replay_bag

    count = replay_bag(path, make_bridge(), speed=speed)
    print(f"replayed {count} messages from {path}")


# -- the no-ROS-required simulation ----------------------------------------


class _Struct:
    """A stand-in for a ROS message, so `--simulate` needs no ROS installation."""

    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


def _vec3(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> _Struct:
    return _Struct(x=x, y=y, z=z)


def _quat_from_yaw(yaw: float) -> _Struct:
    return _Struct(x=0.0, y=0.0, z=math.sin(yaw / 2.0), w=math.cos(yaw / 2.0))


def _header(frame_id: str, stamp: float) -> _Struct:
    return _Struct(
        frame_id=frame_id,
        stamp=_Struct(sec=int(stamp), nanosec=int((stamp % 1.0) * 1e9)),
    )


def _transform(parent: str, child: str, position, yaw: float, stamp: float) -> _Struct:
    return _Struct(
        header=_header(parent, stamp),
        child_frame_id=child,
        transform=_Struct(translation=_vec3(*position), rotation=_quat_from_yaw(yaw)),
    )


def _map_message(stamp: float) -> _Struct:
    """A 64x64 room with a pillar in the middle and unobserved corners."""
    grid = np.full((64, 64), -1, dtype=np.int8)
    grid[4:60, 4:60] = 0
    grid[4:60, 4] = grid[4:60, 59] = grid[4, 4:60] = grid[59, 4:60] = 100
    grid[28:36, 28:36] = 100
    return _Struct(
        header=_header("map", stamp),
        info=_Struct(
            width=64,
            height=64,
            resolution=0.1,
            origin=_Struct(position=_vec3(-3.2, -3.2, 0.0), orientation=_quat_from_yaw(0.0)),
        ),
        data=grid.reshape(-1).tolist(),
    )


def run_simulated(steps: int) -> None:
    """Drive the converters with synthesized messages, so no ROS is needed."""
    bridge = make_bridge()

    bridge.handle_message("/map", "nav_msgs/msg/OccupancyGrid", _map_message(0.0))

    angles = np.linspace(-math.pi, math.pi, 360, endpoint=False)
    for step in range(steps):
        stamp = step / 20.0
        yaw = stamp * 0.4
        position = (1.5 * math.cos(yaw), 1.5 * math.sin(yaw), 0.0)

        bridge.handle_message(
            "/tf",
            "tf2_msgs/msg/TFMessage",
            _Struct(
                transforms=[
                    _transform("world", "odom", (0.0, 0.0, 0.0), 0.0, stamp),
                    _transform("odom", "base_footprint", position, yaw + math.pi / 2, stamp),
                    _transform("base_footprint", "base_scan", (0.0, 0.0, 0.18), 0.0, stamp),
                ]
            ),
        )

        # A scan of a square room, as seen from wherever the robot currently is.
        ranges = 2.2 + 0.6 * np.sin(4.0 * angles + yaw)
        ranges[::37] = np.inf  # the dropouts every real lidar has
        bridge.handle_message(
            "/scan",
            "sensor_msgs/msg/LaserScan",
            _Struct(
                header=_header("base_scan", stamp),
                ranges=ranges.tolist(),
                angle_min=float(angles[0]),
                angle_increment=float(angles[1] - angles[0]),
                range_min=0.1,
                range_max=12.0,
            ),
        )

        bridge.handle_message(
            "/odom",
            "nav_msgs/msg/Odometry",
            _Struct(
                header=_header("odom", stamp),
                pose=_Struct(pose=_Struct(position=_vec3(*position), orientation=_quat_from_yaw(yaw + math.pi / 2))),
                twist=_Struct(twist=_Struct(linear=_vec3(0.6, 0.0, 0.0), angular=_vec3(0.0, 0.0, 0.4))),
            ),
        )

        bridge.handle_message(
            "/imu",
            "sensor_msgs/msg/Imu",
            _Struct(
                header=_header("base_footprint", stamp),
                orientation=_quat_from_yaw(yaw + math.pi / 2),
                orientation_covariance=[0.01] + [0.0] * 8,
                linear_acceleration=_vec3(0.0, 0.24, 9.81),
                angular_velocity=_vec3(0.0, 0.0, 0.4),
            ),
        )

        bridge.handle_message(
            "/battery_state",
            "sensor_msgs/msg/BatteryState",
            _Struct(
                header=_header("base_footprint", stamp),
                percentage=1.0 - step / (steps * 4.0),
                voltage=16.4 - step / (steps * 8.0),
                current=-1.8,
            ),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize a TurtleBot's ROS 2 topics with Dalaran.")
    parser.add_argument(
        "mode",
        nargs="?",
        default="simulate",
        choices=["live", "bag", "simulate"],
        help="Subscribe to a live graph, replay a bag, or synthesize messages without ROS.",
    )
    parser.add_argument("path", nargs="?", help="The bag to replay, for `bag` mode.")
    parser.add_argument("--duration", type=float, default=None, help="Stop live bridging after this many seconds.")
    parser.add_argument("--speed", type=float, default=0.0, help="Bag replay speed; 0 is as fast as possible.")
    parser.add_argument("--steps", type=int, default=400, help="Number of simulated steps.")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_ros2_turtlebot", default_blueprint=blueprint())

    if args.mode == "live":
        run_live(args.duration)
    elif args.mode == "bag":
        if not args.path:
            parser.error("`bag` mode needs a path to a rosbag2 recording")
        run_bag(args.path, args.speed)
    else:
        run_simulated(args.steps)

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
