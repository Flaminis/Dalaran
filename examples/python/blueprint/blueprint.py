#!/usr/bin/env python3
"""Example of using the blueprint APIs to configure Dalaran."""

from __future__ import annotations

import argparse

import numpy as np

import dalaran as dl  # pip install dalaran-sdk
import dalaran.blueprint as dlb


def main() -> None:
    parser = argparse.ArgumentParser(description="Different options for how we might use blueprint")

    parser.add_argument("--skip-blueprint", action="store_true", help="Don't send the blueprint")
    parser.add_argument("--auto-views", action="store_true", help="Automatically add views")

    args = parser.parse_args()

    if args.skip_blueprint:
        blueprint = None
    else:
        # Create a blueprint which includes 2 additional views each only showing 1 of the two
        # rectangles.
        #
        # If auto_views is True, the blueprint will automatically add one of the heuristic
        # views, which will include the image and both rectangles.
        blueprint = dlb.Blueprint(
            dlb.Grid(
                dlb.Spatial2DView(name="Rect 0", origin="/", contents=["image", "rect/0"]),
                dlb.Spatial2DView(
                    name="Rect 1",
                    origin="/",
                    contents=["/**"],
                    defaults=[dl.Boxes2D.from_fields(radii=2)],  # Default all rectangles to have a radius of 2
                    overrides={"rect/0": dl.Boxes2D.from_fields(radii=1)},  # Override the radius of rect/0 to be 1
                ),
            ),
            dlb.BlueprintPanel(state="collapsed"),
            dlb.SelectionPanel(state="collapsed"),
            dlb.TimePanel(
                state="collapsed",
                timeline="custom",
                time_selection=dlb.components.AbsoluteTimeRange(10, 25),
                loop_mode="selection",
                play_state="playing",
            ),
            auto_views=args.auto_views,
        )

    dl.init("dalaran_example_blueprint", spawn=True, default_blueprint=blueprint)

    dl.set_time("custom", sequence=0)

    img = np.zeros([128, 128, 3], dtype="uint8")
    for i in range(8):
        img[(i * 16) + 4 : (i * 16) + 12, :] = (0, 0, 200)
    dl.log("image", dl.Image(img))

    dl.set_time("custom", sequence=10)
    dl.log(
        "rect/0",
        dl.Boxes2D(mins=[16, 16], sizes=[64, 64], labels="Rect0", colors=(255, 0, 0)),
    )

    dl.set_time("custom", sequence=20)
    dl.log(
        "rect/1",
        dl.Boxes2D(mins=[48, 48], sizes=[64, 64], labels="Rect1", colors=(0, 255, 0)),
    )


if __name__ == "__main__":
    main()
