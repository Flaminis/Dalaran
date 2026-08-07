#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Final

import matplotlib
import numpy as np
from nuscenes import nuscenes

import dalaran as dl

from .download_dataset import MINISPLIT_SCENES, download_minisplit

EXAMPLE_DIR: Final = pathlib.Path(__file__).parent.parent
DATASET_DIR: Final = EXAMPLE_DIR / "dataset"

# currently need to calculate the color manually
# see https://github.com/rerun-io/rerun/issues/4409
cmap = matplotlib.colormaps["turbo_r"]
norm = matplotlib.colors.Normalize(
    vmin=3.0,
    vmax=75.0,
)


def ensure_scene_available(root_dir: pathlib.Path, dataset_version: str, scene_name: str) -> None:
    """
    Ensure that the specified scene is available.

    Downloads minisplit into root_dir if scene_name is part of it and root_dir is empty.

    Raises ValueError if scene is not available and cannot be downloaded.
    """
    try:
        nusc = nuscenes.NuScenes(version=dataset_version, dataroot=root_dir, verbose=True)
    except AssertionError:  # dataset initialization failed
        if dataset_version == "v1.0-mini" and scene_name in MINISPLIT_SCENES:
            download_minisplit(root_dir)
            nusc = nuscenes.NuScenes(version=dataset_version, dataroot=root_dir, verbose=True)
        else:
            print(f"Could not find dataset at {root_dir} and could not automatically download specified scene.")
            sys.exit()

    scene_names = [s["name"] for s in nusc.scene]
    if scene_name not in scene_names:
        raise ValueError(f"{scene_name=} not found in dataset")


def log_nuscenes_lidar(root_dir: pathlib.Path, dataset_version: str, scene_name: str) -> None:
    nusc = nuscenes.NuScenes(version=dataset_version, dataroot=root_dir, verbose=True)

    scene = next(s for s in nusc.scene if s["name"] == scene_name)

    dl.log("world", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    first_sample = nusc.get("sample", scene["first_sample_token"])
    current_lidar_token = first_sample["data"]["LIDAR_TOP"]
    while current_lidar_token != "":
        sample_data = nusc.get("sample_data", current_lidar_token)

        data_file_path = nusc.dataroot / sample_data["filename"]
        pointcloud = nuscenes.LidarPointCloud.from_file(str(data_file_path))
        points = pointcloud.points[:3].T  # shape after transposing: (num_points, 3)
        point_distances = np.linalg.norm(points, axis=1)
        point_colors = cmap(norm(point_distances))

        # timestamps are in microseconds
        dl.set_time("timestamp", timestamp=sample_data["timestamp"] * 1e-6)
        dl.log("world/lidar", dl.Points3D(points, colors=point_colors))

        current_lidar_token = sample_data["next"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualizes lidar scans using the Dalaran SDK.")
    parser.add_argument(
        "--root-dir",
        type=pathlib.Path,
        default=DATASET_DIR,
        help="Root directory of nuScenes dataset",
    )
    parser.add_argument(
        "--scene-name",
        type=str,
        default="scene-0061",
        help="Scene name to visualize (typically of form 'scene-xxxx')",
    )
    parser.add_argument("--dataset-version", type=str, default="v1.0-mini", help="Scene id to visualize")
    dl.script_add_args(parser)
    args = parser.parse_args()

    ensure_scene_available(args.root_dir, args.dataset_version, args.scene_name)

    dl.script_setup(args, "dalaran_example_lidar")
    log_nuscenes_lidar(args.root_dir, args.dataset_version, args.scene_name)

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
