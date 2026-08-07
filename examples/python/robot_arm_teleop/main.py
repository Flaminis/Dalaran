#!/usr/bin/env python3
"""
Teleoperating a mobile manipulator with the `dalaran.robot` API.

A differential-drive base follows a figure-eight while a three-joint arm mounted
on it tracks a moving target. Everything - the transform tree, the joint
animation, the lidar scan, the camera and the IMU - goes through
[`dalaran.robot`][], so the example doubles as a tour of that API.
"""

from __future__ import annotations

import argparse

import numpy as np
import numpy.typing as npt

import dalaran as dl  # pip install dalaran-sdk

# Robot geometry, in meters.
BASE_HEIGHT = 0.25
SHOULDER_HEIGHT = 0.35
UPPER_ARM = 0.45
FOREARM = 0.35

LIDAR_BEAMS = 360
LIDAR_RANGE = 8.0

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FX = 260.0


def figure_eight(t: float) -> tuple[npt.NDArray[np.float64], float]:
    """
    Return the base position and heading along a figure-eight at time `t`.

    The heading is the tangent of the path, which is what a differential-drive
    base would actually do.
    """
    position = np.array([2.0 * np.sin(t), 1.5 * np.sin(2.0 * t), 0.0])
    velocity = np.array([2.0 * np.cos(t), 3.0 * np.cos(2.0 * t), 0.0])
    return position, float(np.arctan2(velocity[1], velocity[0]))


def arm_joint_positions(t: float) -> list[float]:
    """Return the three arm joint angles, in radians, at time `t`."""
    return [
        0.8 * np.sin(0.7 * t),
        -0.6 + 0.5 * np.sin(0.9 * t + 1.0),
        1.1 + 0.6 * np.sin(1.3 * t),
    ]


def simulated_lidar_scan(heading: float, position: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    Return `LIDAR_BEAMS` ranges for a robot standing inside a square room.

    Beams that would hit nothing within `LIDAR_RANGE` come back as `inf`, exactly
    like a real driver reports them; `dalaran.robot.log_lidar_scan` drops those.
    """
    room = 6.0
    angles = np.linspace(-np.pi, np.pi, LIDAR_BEAMS, endpoint=False) + heading
    cos, sin = np.cos(angles), np.sin(angles)

    with np.errstate(divide="ignore", invalid="ignore"):
        candidates = np.stack([
            (room - position[0]) / cos,
            (-room - position[0]) / cos,
            (room - position[1]) / sin,
            (-room - position[1]) / sin,
        ])
    candidates = np.where(candidates > 0.0, candidates, np.inf)
    ranges = np.nanmin(candidates, axis=0)

    # Simulate dropouts and out-of-range returns.
    ranges[ranges > LIDAR_RANGE] = np.inf
    ranges[::37] = np.inf
    return ranges


def simulated_camera_image(t: float) -> npt.NDArray[np.uint8]:
    """Return a cheap synthetic RGB image so the pinhole frustum has something in it."""
    ys, xs = np.mgrid[0:CAMERA_HEIGHT, 0:CAMERA_WIDTH]
    r = (127.0 + 127.0 * np.sin(xs / 40.0 + t)).astype(np.uint8)
    g = (127.0 + 127.0 * np.sin(ys / 40.0 + t * 0.7)).astype(np.uint8)
    b = np.full_like(r, 90)
    return np.stack([r, g, b], axis=-1)


def build_robot() -> dl.robot.Robot:
    """Declare the robot's frames and joints once, up front."""
    robot = dl.robot.Robot("mobile_manipulator", base_frame="base_link")

    # Sensors are bolted on, so their transforms are static.
    robot.tree.add("lidar", parent="base_link")
    robot.tree.set("lidar", translation=[0.15, 0.0, BASE_HEIGHT + 0.1], static=True)

    robot.tree.add("imu", parent="base_link")
    robot.tree.set("imu", translation=[0.0, 0.0, BASE_HEIGHT], static=True)

    # The camera is an RDF optical frame, so it needs the optical rotation
    # relative to the FLU body frame. Getting this wrong is the classic
    # "my camera looks 90 degrees off" bug.
    robot.tree.add("camera", parent="base_link")
    robot.tree.set(
        "camera",
        translation=[0.25, 0.0, BASE_HEIGHT + 0.05],
        rotation_matrix=dl.robot.convention_matrix(dl.robot.FLU, dl.robot.RDF).T,
        static=True,
    )

    # A three-joint arm: yaw at the shoulder, then two pitching links.
    robot.add_joint("shoulder_pan", parent="base_link", origin=[0.0, 0.0, SHOULDER_HEIGHT], axis=[0, 0, 1])
    robot.add_joint("shoulder_lift", parent="shoulder_pan", origin=[0.0, 0.0, 0.1], axis=[0, 1, 0])
    robot.add_joint("elbow", parent="shoulder_lift", origin=[0.0, 0.0, UPPER_ARM], axis=[0, 1, 0])

    robot.tree.add("gripper", parent="elbow")
    robot.tree.set("gripper", translation=[0.0, 0.0, FOREARM], static=True)

    return robot


def log_arm_links(robot: dl.robot.Robot) -> None:
    """Draw the arm links as line strips in each joint's own frame."""
    for frame, length in (("shoulder_lift", UPPER_ARM), ("elbow", FOREARM)):
        dl.log(
            robot.tree.entity_path(frame),
            dl.LineStrips3D([[[0.0, 0.0, 0.0], [0.0, 0.0, length]]], colors=[(160, 200, 255)], radii=0.03),
            static=True,
        )


def run(steps: int) -> None:
    robot = build_robot()
    log_arm_links(robot)

    # The floor of the room, drawn once in the world frame.
    dl.log("world/floor", dl.Boxes3D(half_sizes=[[6.0, 6.0, 0.01]], colors=[(40, 40, 48)]), static=True)

    for step in range(steps):
        t = step / 20.0
        with robot.timestep(t):
            position, heading = figure_eight(t)
            position = position + [0.0, 0.0, BASE_HEIGHT]

            robot.log_odometry(
                position=position,
                rpy=[0.0, 0.0, heading],
                linear_velocity=[1.0, 0.0, 0.0],
                angular_velocity=[0.0, 0.0, float(np.cos(t))],
            )

            joints = arm_joint_positions(t)
            robot.log_joint_states(
                ["shoulder_pan", "shoulder_lift", "elbow"],
                joints,
                velocities=np.gradient(joints).tolist(),
            )

            dl.robot.log_lidar_scan(
                robot.tree.entity_path("lidar"),
                simulated_lidar_scan(heading, position),
                angle_min=-np.pi,
                angle_increment=2.0 * np.pi / LIDAR_BEAMS,
                range_max=LIDAR_RANGE,
                colorize_by_range=True,
            )

            dl.robot.log_imu(
                robot.tree.entity_path("imu"),
                linear_acceleration=[0.2 * np.cos(t), 0.2 * np.sin(t), 9.81],
                angular_velocity=[0.0, 0.0, float(np.cos(t))],
            )

            if step % 5 == 0:
                dl.robot.log_camera(
                    robot.tree.entity_path("camera"),
                    width=CAMERA_WIDTH,
                    height=CAMERA_HEIGHT,
                    fx=CAMERA_FX,
                    image=simulated_camera_image(t),
                    image_plane_distance=0.5,
                )

        # `lookup` answers the tf2 question directly: where is the gripper in the world?
        if step == steps - 1:
            world_from_gripper = robot.tree.lookup("world", "gripper")
            print(f"final gripper position in world: {np.round(world_from_gripper[:3, 3], 3)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Teleoperating a mobile manipulator with the high-level dalaran.robot API.",
    )
    parser.add_argument("--steps", type=int, default=400, help="The number of time steps to log")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_robot_arm_teleop")
    run(args.steps)
    dl.script_teardown(args)


if __name__ == "__main__":
    main()
