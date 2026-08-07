#!/usr/bin/env python3
"""A minimal example of streaming frames live from an Intel RealSense depth sensor."""

from __future__ import annotations

import argparse

import numpy as np
import pyrealsense2 as rs

import dalaran as dl  # pip install dalaran-sdk


def run_realsense(num_frames: int | None) -> None:
    # Visualize the data as RDF
    dl.log("realsense", dl.ViewCoordinates.RDF, static=True)

    # Open the pipe
    pipe = rs.pipeline()
    profile = pipe.start()

    # We don't log the depth exstrinsics. We treat the "realsense" space as being at
    # the origin of the depth sensor so that "realsense/depth" = Identity

    # Get and log depth intrinsics
    depth_profile = profile.get_stream(rs.stream.depth)
    depth_intr = depth_profile.as_video_stream_profile().get_intrinsics()

    dl.log(
        "realsense/depth/image",
        dl.Pinhole(
            resolution=[depth_intr.width, depth_intr.height],
            focal_length=[depth_intr.fx, depth_intr.fy],
            principal_point=[depth_intr.ppx, depth_intr.ppy],
        ),
        static=True,
    )

    # Get and log color extrinsics
    rgb_profile = profile.get_stream(rs.stream.color)

    rgb_from_depth = depth_profile.get_extrinsics_to(rgb_profile)
    dl.log(
        "realsense/rgb",
        dl.Transform3D(
            translation=rgb_from_depth.translation,
            mat3x3=np.reshape(rgb_from_depth.rotation, (3, 3)),
            relation=dl.TransformRelation.ChildFromParent,
        ),
        static=True,
    )

    # Get and log color intrinsics
    rgb_intr = rgb_profile.as_video_stream_profile().get_intrinsics()

    dl.log(
        "realsense/rgb/image",
        dl.Pinhole(
            resolution=[rgb_intr.width, rgb_intr.height],
            focal_length=[rgb_intr.fx, rgb_intr.fy],
            principal_point=[rgb_intr.ppx, rgb_intr.ppy],
        ),
        static=True,
    )

    # Read frames in a loop
    frame_nr = 0
    try:
        while True:
            if num_frames and frame_nr >= num_frames:
                break

            dl.set_time("frame_nr", sequence=frame_nr)
            frame_nr += 1

            frames = pipe.wait_for_frames()
            for _f in frames:
                # Log the depth frame
                depth_frame = frames.get_depth_frame()
                depth_units = depth_frame.get_units()
                depth_image = np.asanyarray(depth_frame.get_data())
                dl.log("realsense/depth/image", dl.DepthImage(depth_image, meter=1.0 / depth_units))

                # Log the color frame
                color_frame = frames.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data())
                dl.log("realsense/rgb/image", dl.Image(color_image))
    finally:
        pipe.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Streams frames from a connected realsense depth sensor.")
    parser.add_argument("--num-frames", type=int, default=None, help="The number of frames to log")

    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_live_depth_sensor")

    run_realsense(args.num_frames)

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
