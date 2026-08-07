#!/usr/bin/env python3
"""Pick and place with an SO-100 arm, logged to Dalaran.

Real data from `lerobot/svla_so100_pickplace` on the Hugging Face LeRobot hub:
a 6-DoF SO-100 arm picking up a cube and dropping it in a box, recorded at 30 Hz
with an overhead camera and a wrist camera.

Everything here is real: the joint trajectories, the gripper, both videos, and the
robot model itself (the SO-ARM100 URDF with its STL meshes, which ships in this
repository). The joint angles drive the actual URDF, so the arm you see in 3D is
the arm that recorded the video next to it.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

import dalaran as dl
import dalaran.blueprint as dlb
from dalaran.robot import Robot

REPO = "lerobot/svla_so100_pickplace"
BASE = f"https://huggingface.co/datasets/{REPO}/resolve/main"
FILES = {
    "info.json": "meta/info.json",
    "data.parquet": "data/chunk-000/file-000.parquet",
    "top.mp4": "videos/observation.images.top/chunk-000/file-000.mp4",
    "wrist.mp4": "videos/observation.images.wrist/chunk-000/file-000.mp4",
}

# The SO-100 URDF names its joints "1".."6"; the dataset names the same six motors.
JOINT_FOR_MOTOR = {
    "main_shoulder_pan": "1",
    "main_shoulder_lift": "2",
    "main_elbow_flex": "3",
    "main_wrist_flex": "4",
    "main_wrist_roll": "5",
    "main_gripper": "6",
}

# Camera frames. The overhead camera is bolted to the world; the wrist camera rides
# the gripper link, so it has to hang off that frame to move with the arm.
TOP_CAM = ("world/camera_top", "camera_top", "base")
WRIST_CAM = ("world/camera_wrist", "camera_wrist", "gripper")


def fetch_dataset(root: Path) -> None:
    """Download the dataset files this example needs, if they are not already there."""
    root.mkdir(parents=True, exist_ok=True)
    for local, remote in FILES.items():
        target = root / local
        if target.exists():
            continue
        print(f"downloading {remote} …")
        urllib.request.urlretrieve(f"{BASE}/{remote}", target)  # noqa: S310


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


def log_camera(
    entity: str,
    frame: str,
    parent_frame: str,
    video_path: Path,
    *,
    translation: tuple[float, float, float],
    rpy: tuple[float, float, float],
    n_frames: int,
) -> None:
    """Log a video stream as a camera that is part of the robot's frame graph.

    A camera has to be reachable in the FRAME graph, not just the entity hierarchy:
    the URDF publishes frame-based transforms, and the 3D view resolves against
    those. An entity without a `CoordinateFrame` and a `parent_frame`/`child_frame`
    transform shows up as "No transform path from ... to the view's target frame".
    """
    dl.log(
        "tf_static",
        dl.Transform3D(
            translation=translation,
            quaternion=quaternion_from_rpy(*rpy),
            parent_frame=parent_frame,
            child_frame=frame,
        ),
        static=True,
    )
    dl.log(entity, dl.CoordinateFrame(frame=frame), static=True)

    video = dl.AssetVideo(path=video_path)
    dl.log(entity, video, static=True)
    dl.log(
        entity,
        dl.Pinhole(
            width=640,
            height=480,
            focal_length=430.0,
            camera_xyz=dl.ViewCoordinates.RDF,
            image_plane_distance=0.12,
        ),
        static=True,
    )
    nanos = video.read_frame_timestamps_nanos()
    take = min(len(nanos), n_frames)
    dl.send_columns(
        entity,
        indexes=[dl.TimeColumn("time", duration=1e-9 * nanos[:take])],
        columns=dl.VideoFrameReference.columns_nanos(nanos[:take]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=int, default=0, help="which episode to log")
    parser.add_argument("--dataset-dir", type=Path, default=Path("dataset"), help="dataset cache")
    parser.add_argument("--urdf", type=Path, default=None, help="path to so100.urdf")
    parser.add_argument("--save", type=Path, default=None, help="write a .dlr instead of spawning a viewer")
    args = parser.parse_args()

    urdf = args.urdf or (Path(__file__).resolve().parents[2] / "rust" / "animated_urdf" / "data" / "so100.urdf")
    if not urdf.exists() or urdf.stat().st_size < 4096:
        msg = (
            f"{urdf} is missing or is still a git-LFS pointer.\n"
            "Run `git lfs pull --include='examples/rust/animated_urdf/data/**'` first, "
            "or pass --urdf with your own SO-100 URDF."
        )
        raise SystemExit(msg)

    fetch_dataset(args.dataset_dir)
    info = json.loads((args.dataset_dir / "info.json").read_text())
    motors = info["features"]["observation.state"]["names"]
    joints = [JOINT_FOR_MOTOR[m] for m in motors]

    table = pq.read_table(args.dataset_dir / "data.parquet")
    mask = table.column("episode_index").to_numpy() == args.episode
    # The SO-100 reports degrees; the URDF is in radians.
    state = np.deg2rad(np.stack(table.column("observation.state").to_pylist())[mask])
    action = np.deg2rad(np.stack(table.column("action").to_pylist())[mask])
    stamps = table.column("timestamp").to_numpy()[mask]

    dl.init("dalaran_so100_pickplace", spawn=args.save is None)
    if args.save is not None:
        dl.save(args.save)

    dl.send_blueprint(
        dlb.Blueprint(
            dlb.Horizontal(
                dlb.Spatial3DView(
                    origin="/world",
                    name="SO-100 (real URDF, real joint states)",
                    eye_controls=dlb.EyeControls3D(
                        kind=dlb.Eye3DKind.Orbital,
                        position=(0.55, -0.55, 0.42),
                        look_target=(0.0, 0.0, 0.12),
                        eye_up=(0.0, 0.0, 1.0),
                    ),
                ),
                dlb.Vertical(
                    dlb.Horizontal(
                        dlb.Spatial2DView(origin=TOP_CAM[0], name="Overhead camera"),
                        dlb.Spatial2DView(origin=WRIST_CAM[0], name="Wrist camera"),
                    ),
                    dlb.TimeSeriesView(origin="/joints", name="Joints: commanded vs measured"),
                    dlb.TextDocumentView(origin="/task", name="Task"),
                    row_shares=[3, 3, 1],
                ),
                column_shares=[3, 4],
            ),
            collapse_panels=False,
        )
    )

    dl.log("/", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
    dl.log(
        "task",
        dl.TextDocument(
            "# Pick up the cube and place it in the box\n\n"
            f"* dataset: `{REPO}`\n"
            f"* robot: {info['robot_type']}, {len(motors)} joints, {info['fps']} Hz\n"
            f"* episode {args.episode}: {int(mask.sum())} frames "
            f"({stamps[-1] - stamps[0]:.1f} s)\n"
            "* the 3D arm is the real SO-ARM100 URDF, driven by the recorded joint angles\n",
            media_type=dl.MediaType.MARKDOWN,
        ),
        static=True,
    )

    robot = Robot("so100", base_frame="base", root_frame="world", urdf=urdf, timeline="time")

    n = int(mask.sum())
    log_camera(
        *TOP_CAM, args.dataset_dir / "top.mp4", translation=(0.32, 0.0, 0.42), rpy=(0.0, 1.15, np.pi), n_frames=n
    )
    log_camera(
        *WRIST_CAM, args.dataset_dir / "wrist.mp4", translation=(0.0, 0.0, 0.04), rpy=(0.0, 0.0, 0.0), n_frames=n
    )

    for i, t in enumerate(stamps):
        with robot.timestep(float(t)):
            robot.log_joint_states(joints, state[i])
            for motor, measured, commanded in zip(motors, state[i], action[i]):
                short = motor.removeprefix("main_")
                dl.log(f"joints/{short}/measured", dl.Scalars(float(measured)))
                dl.log(f"joints/{short}/commanded", dl.Scalars(float(commanded)))
            dl.log("metrics/tracking_error", dl.Scalars(float(np.abs(action[i] - state[i]).mean())))

    print(f"logged episode {args.episode}: {n} frames, {len(joints)} joints")


if __name__ == "__main__":
    main()
