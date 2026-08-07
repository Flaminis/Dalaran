#!/usr/bin/env python3
"""
Very simple example of capturing from a live camera.

Runs the opencv canny edge detector on the image stream.
"""

from __future__ import annotations

import argparse

import cv2

import dalaran as dl  # pip install dalaran-sdk
import dalaran.blueprint as dlb


def run_canny(num_frames: int | None) -> None:
    # Create a new video capture
    cap = cv2.VideoCapture(0)

    frame_nr = 0

    while cap.isOpened():
        if num_frames and frame_nr >= num_frames:
            break

        # Read the frame
        ret, img = cap.read()
        if not ret:
            if frame_nr == 0:
                print("Failed to capture any frame. No camera connected?")
            else:
                print("Can't receive frame (stream end?). Exiting…")
            break

        # Get the current frame time. On some platforms it always returns zero.
        frame_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        if frame_time_ms != 0:
            dl.set_time("frame_time", duration=1e-3 * frame_time_ms)

        dl.set_time("frame_nr", sequence=frame_nr)
        frame_nr += 1

        # Log the original image
        dl.log("image/rgb", dl.Image(img, color_model="BGR"))

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dl.log("image/gray", dl.Image(gray))

        # Run the canny edge detector
        canny = cv2.Canny(gray, 50, 200)
        dl.log("image/canny", dl.Image(canny))


def main() -> None:
    parser = argparse.ArgumentParser(description="Streams a local system camera and runs the canny edge detector.")
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="Which camera device to use. (Passed to `cv2.VideoCapture()`)",
    )
    parser.add_argument("--num-frames", type=int, default=None, help="The number of frames to log")

    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(
        args,
        "dalaran_example_live_camera_edge_detection",
        default_blueprint=dlb.Vertical(
            dlb.Horizontal(
                dlb.Spatial2DView(origin="/image/rgb", name="Video"),
                dlb.Spatial2DView(origin="/image/gray", name="Video (Grayscale)"),
            ),
            dlb.Spatial2DView(origin="/image/canny", name="Canny Edge Detector"),
            row_shares=[1, 2],
        ),
    )

    run_canny(args.num_frames)

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
