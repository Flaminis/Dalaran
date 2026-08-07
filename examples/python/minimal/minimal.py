#!/usr/bin/env python3
"""Demonstrates the most barebone usage of the Dalaran SDK."""

from __future__ import annotations

import sys

import numpy as np

import dalaran as dl  # pip install dalaran-sdk


def main() -> None:
    # sanity-check since all other example scripts take arguments:
    assert len(sys.argv) == 1, f"{sys.argv[0]} does not take any arguments"

    dl.init("dalaran_example_minimal", spawn=True)

    positions = np.vstack([xyz.ravel() for xyz in np.mgrid[3 * [slice(-10, 10, 10j)]]]).T
    colors = np.vstack([rgb.ravel() for rgb in np.mgrid[3 * [slice(0, 255, 10j)]]]).astype(np.uint8).T

    dl.log("my_points", dl.Points3D(positions, colors=colors, radii=0.5))


if __name__ == "__main__":
    main()
