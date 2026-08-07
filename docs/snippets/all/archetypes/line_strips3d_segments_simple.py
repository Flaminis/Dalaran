#!/usr/bin/env python3
"""Log a simple set of line segments."""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_line_segments3d", spawn=True)

dl.log(
    "segments",
    dl.LineStrips3D(
        np.array(
            [
                [[0, 0, 0], [0, 0, 1]],
                [[1, 0, 0], [1, 0, 1]],
                [[1, 1, 0], [1, 1, 1]],
                [[0, 1, 0], [0, 1, 1]],
            ],
        ),
    ),
)
