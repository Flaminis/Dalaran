#!/usr/bin/env python3
"""Demonstrates the most barebone usage of the Dalaran SDK, with standard options."""

from __future__ import annotations

import argparse

import numpy as np

import dalaran as dl  # pip install dalaran-sdk


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstrates the most barebone usage of the Dalaran SDK, with standard options.",
    )
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_minimal_options")

    positions = np.vstack([xyz.ravel() for xyz in np.mgrid[3 * [slice(-10, 10, 10j)]]]).T
    colors = np.vstack([rgb.ravel() for rgb in np.mgrid[3 * [slice(0, 255, 10j)]]]).astype(np.uint8).T

    dl.log("my_points", dl.Points3D(positions, colors=colors, radii=0.5))

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
