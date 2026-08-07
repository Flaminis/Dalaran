#!/usr/bin/env python3
"""Log a real ALOHA bimanual-manipulation episode into Dalaran.

Data: `lerobot/aloha_sim_transfer_cube_human` from the Hugging Face LeRobot hub
(50 Hz, 14 joints across two 6-DoF arms plus grippers, one overhead camera).

The joint trajectories, gripper motion, actions and camera video are all real
recorded data. The link geometry is an approximation of a ViperX-style arm,
because the dataset ships joint states rather than a URDF; the motion you see is
the robot's, the tube lengths are ours.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

import dalaran as dl
from dalaran.robot import Robot

REPO = "lerobot/aloha_sim_transfer_cube_human"
BASE = f"https://huggingface.co/datasets/{REPO}/resolve/main"
FILES = {
    "info.json": "meta/info.json",
    "data.parquet": "data/chunk-000/file-000.parquet",
    "top.mp4": "videos/observation.images.top/chunk-000/file-000.mp4",
}


def fetch_dataset(root: Path) -> None:
    """Download the three files this example needs, if they are not already there."""
    root.mkdir(parents=True, exist_ok=True)
    for local, remote in FILES.items():
        target = root / local
        if target.exists():
            continue
        print(f"downloading {remote} …")
        urllib.request.urlretrieve(f"{BASE}/{remote}", target)  # noqa: S310


CAMERA_FRAME = "camera_top"
CAMERA_PATH = "world/camera_top"
# The URDF's root link name is also its frame name, and it is the frame the 3D view
# targets, so the camera hangs off it.
ROBOT_ROOT_FRAME = "torso"


def quaternion_from_rpy(roll: float, pitch: float, yaw: float) -> tuple[float, float, float, float]:
    """Fixed-axis RPY to an `xyzw` quaternion, matching REP-103 and URDF."""
    cr, sr = np.cos(roll / 2), np.sin(roll / 2)
    cp, sp = np.cos(pitch / 2), np.sin(pitch / 2)
    cy, sy = np.cos(yaw / 2), np.sin(yaw / 2)
    return (
        float(sr * cp * cy - cr * sp * sy),
        float(cr * sp * cy + sr * cp * sy),
        float(cr * cp * sy - sr * sp * cy),
        float(cr * cp * cy + sr * sp * sy),
    )


def _box(x, y, z, ox=0.0, oy=0.0, oz=0.0, rgba="0.55 0.58 0.68 1"):
    return (
        f'<visual><origin xyz="{ox} {oy} {oz}"/><geometry>'
        f'<box size="{x} {y} {z}"/></geometry>'
        f'<material name="steel"><color rgba="{rgba}"/></material></visual>'
    )


def _cyl(r, h, ox=0.0, oy=0.0, oz=0.0, rgba="0.42 0.30 0.94 1"):
    return (
        f'<visual><origin xyz="{ox} {oy} {oz}"/><geometry>'
        f'<cylinder radius="{r}" length="{h}"/></geometry>'
        f'<material name="violet"><color rgba="{rgba}"/></material></visual>'
    )


ARM = (
    """
  <link name="{s}_base">"""
    + _cyl(0.045, 0.08, oz=0.04)
    + """</link>
  <link name="{s}_shoulder">"""
    + _box(0.26, 0.07, 0.07, ox=0.13)
    + """</link>
  <link name="{s}_upper">"""
    + _box(0.26, 0.06, 0.06, ox=0.13)
    + """</link>
  <link name="{s}_elbow">"""
    + _cyl(0.032, 0.07, ox=0.035)
    + """</link>
  <link name="{s}_roll">"""
    + _box(0.06, 0.05, 0.05, ox=0.03)
    + """</link>
  <link name="{s}_wrist">"""
    + _cyl(0.028, 0.05, ox=0.025)
    + """</link>
  <link name="{s}_hand">"""
    + _box(0.06, 0.012, 0.03, ox=0.03, rgba="0.91 0.71 0.29 1")
    + """</link>
  <link name="{s}_finger">"""
    + _box(0.06, 0.012, 0.03, ox=0.03, rgba="0.91 0.71 0.29 1")
    + """</link>
  <joint name="{s}_waist" type="revolute">
    <parent link="torso"/><child link="{s}_base"/>
    <origin xyz="0 {y} 0.10"/><axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="10" velocity="3"/></joint>
  <joint name="{s}_shoulder" type="revolute">
    <parent link="{s}_base"/><child link="{s}_shoulder"/>
    <origin xyz="0 0 0.08"/><axis xyz="0 1 0"/>
    <limit lower="-1.85" upper="1.26" effort="10" velocity="3"/></joint>
  <joint name="{s}_elbow" type="revolute">
    <parent link="{s}_shoulder"/><child link="{s}_upper"/>
    <origin xyz="0.26 0 0"/><axis xyz="0 1 0"/>
    <limit lower="-1.76" upper="1.6" effort="10" velocity="3"/></joint>
  <joint name="{s}_forearm_roll" type="revolute">
    <parent link="{s}_upper"/><child link="{s}_elbow"/>
    <origin xyz="0.26 0 0"/><axis xyz="1 0 0"/>
    <limit lower="-3.14" upper="3.14" effort="5" velocity="3"/></joint>
  <joint name="{s}_wrist_angle" type="revolute">
    <parent link="{s}_elbow"/><child link="{s}_roll"/>
    <origin xyz="0.07 0 0"/><axis xyz="0 1 0"/>
    <limit lower="-1.8" upper="2.2" effort="5" velocity="3"/></joint>
  <joint name="{s}_wrist_rotate" type="revolute">
    <parent link="{s}_roll"/><child link="{s}_wrist"/>
    <origin xyz="0.06 0 0"/><axis xyz="1 0 0"/>
    <limit lower="-3.14" upper="3.14" effort="5" velocity="3"/></joint>
  <joint name="{s}_gripper" type="prismatic">
    <parent link="{s}_wrist"/><child link="{s}_hand"/>
    <origin xyz="0.05 0 0.018"/><axis xyz="0 1 0"/>
    <limit lower="0" upper="0.04" effort="5" velocity="1"/></joint>
  <joint name="{s}_gripper_mirror" type="prismatic">
    <parent link="{s}_wrist"/><child link="{s}_finger"/>
    <origin xyz="0.05 0 -0.018"/><axis xyz="0 1 0"/>
    <mimic joint="{s}_gripper" multiplier="-1.0" offset="0.0"/>
    <limit lower="-0.04" upper="0" effort="5" velocity="1"/></joint>
"""
)
URDF = (
    '<robot name="aloha"><link name="torso">'
    + _box(0.18, 0.52, 0.10, oz=0.05, rgba="0.20 0.22 0.28 1")
    + "</link>"
    + ARM.format(s="left", y="0.22")
    + ARM.format(s="right", y="-0.22")
    + "</robot>"
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--episode", type=int, default=0, help="which episode to log")
parser.add_argument("--dataset-dir", type=Path, default=Path("dataset"), help="where to cache the dataset")
parser.add_argument("--save", type=Path, default=None, help="write a .dlr instead of spawning a viewer")
args = parser.parse_args()

ROOT = args.dataset_dir
EPISODE = args.episode
fetch_dataset(ROOT)

info = json.loads((ROOT / "info.json").read_text())
motors = info["features"]["observation.state"]["names"]["motors"]
fps = info["fps"]

table = pq.read_table(ROOT / "data.parquet")
episode = table.column("episode_index").to_numpy() == EPISODE
state = np.stack(table.column("observation.state").to_pylist())[episode]
action = np.stack(table.column("action").to_pylist())[episode]
stamps = table.column("timestamp").to_numpy()[episode]

dl.init("dalaran_aloha_transfer_cube", spawn=args.save is None)
if args.save is not None:
    dl.save(args.save)
dl.log("/", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
dl.log(
    "task",
    dl.TextDocument(
        f"# ALOHA — transfer cube\n\n"
        f"* dataset: `lerobot/aloha_sim_transfer_cube_human`\n"
        f"* robot: {info['robot_type']}, {len(motors)} joints, {fps} Hz\n"
        f"* episode {EPISODE}: {episode.sum()} frames "
        f"({stamps[-1] - stamps[0]:.1f} s of real teleoperation)\n",
        media_type=dl.MediaType.MARKDOWN,
    ),
    static=True,
)

import dalaran.blueprint as dlb

dl.send_blueprint(
    dlb.Blueprint(
        dlb.Horizontal(
            dlb.Vertical(
                dlb.Spatial3DView(
                    origin="/world",
                    name="ALOHA (URDF, real joint states)",
                    # Frame both arms from the front-left; the auto-fit ends up
                    # inside the torso box because the scene is only ~1 m across.
                    eye_controls=dlb.EyeControls3D(
                        kind=dlb.Eye3DKind.Orbital,
                        position=(1.15, -1.05, 0.85),
                        look_target=(0.28, 0.0, 0.22),
                        eye_up=(0.0, 0.0, 1.0),
                    ),
                ),
                dlb.TextDocumentView(origin="/task", name="Episode"),
                row_shares=[3, 1],
            ),
            dlb.Vertical(
                dlb.Spatial2DView(origin=CAMERA_PATH, name="Overhead camera"),
                dlb.TimeSeriesView(origin="/joints/left", name="Left arm joints"),
                dlb.TimeSeriesView(origin="/joints/right", name="Right arm joints"),
                dlb.TimeSeriesView(origin="/gripper", name="Grippers"),
                row_shares=[3, 2, 2, 1],
            ),
            column_shares=[3, 2],
        ),
        collapse_panels=False,
    )
)

robot = Robot("aloha", base_frame="torso", root_frame="world", urdf=URDF, timeline="time")

# The overhead camera is a real video. Three things it needs to sit correctly in
# the scene:
#
# 1. Its frames are indexed on the SAME timeline as the robot ("time"), otherwise a
#    view showing this entity on the robot's timeline has nothing to display.
#    Episode 0 is the head of the video, so the timestamps line up.
# 2. It has to join the FRAME graph, not just the entity hierarchy. The URDF logger
#    publishes frame-based transforms (`Transform3D` carrying `parent_frame` and
#    `child_frame`, plus a `CoordinateFrame` per entity), and the 3D view resolves
#    everything against that graph. An entity that only has a parent/child transform
#    from the entity hierarchy is not reachable there, which is what
#    "No transform path from tf#/world/camera_top to the view's target frame
#    (torso)" means.
# 3. A Pinhole, so it draws as a frustum in 3D rather than only existing as a 2D view.
dl.log(
    "tf_static",
    dl.Transform3D(
        translation=(0.35, 0.0, 1.05),
        # Look down at the table: the optical frame is RDF, so +Z points along world -Z.
        quaternion=quaternion_from_rpy(0.0, np.pi / 2, 0.0),
        parent_frame=ROBOT_ROOT_FRAME,
        child_frame=CAMERA_FRAME,
    ),
    static=True,
)
dl.log(CAMERA_PATH, dl.CoordinateFrame(frame=CAMERA_FRAME), static=True)

video = dl.AssetVideo(path=ROOT / "top.mp4")
dl.log(CAMERA_PATH, video, static=True)
dl.log(
    CAMERA_PATH,
    dl.Pinhole(
        width=640,
        height=480,
        focal_length=420.0,
        camera_xyz=dl.ViewCoordinates.RDF,
        image_plane_distance=0.45,
    ),
    static=True,
)
frame_nanos = video.read_frame_timestamps_nanos()
n_frames = min(len(frame_nanos), int(episode.sum()))
dl.send_columns(
    CAMERA_PATH,
    indexes=[dl.TimeColumn("time", duration=1e-9 * frame_nanos[:n_frames])],
    columns=dl.VideoFrameReference.columns_nanos(frame_nanos[:n_frames]),
)


for i, t in enumerate(stamps):
    with robot.timestep(float(t)):
        robot.log_joint_states(motors, state[i])
        for name, pos, act in zip(motors, state[i], action[i]):
            side, joint = name.split("_", 1)
            dl.log(f"joints/{side}/{joint}/measured", dl.Scalars(float(pos)))
            dl.log(f"joints/{side}/{joint}/commanded", dl.Scalars(float(act)))
        dl.log("gripper/left", dl.Scalars(float(state[i][motors.index("left_gripper")])))
        dl.log("gripper/right", dl.Scalars(float(state[i][motors.index("right_gripper")])))
        err = float(np.abs(action[i] - state[i]).mean())
        dl.log("metrics/tracking_error", dl.Scalars(err))

print(f"logged episode {EPISODE}: {episode.sum()} frames, {len(motors)} joints")
