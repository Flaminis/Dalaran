"""Log a simple line strip."""

import dalaran as dl

dl.init("dalaran_example_line_strip3d", spawn=True)

points = [
    [0, 0, 0],
    [0, 0, 1],
    [1, 0, 0],
    [1, 0, 1],
    [1, 1, 0],
    [1, 1, 1],
    [0, 1, 0],
    [0, 1, 1],
]

dl.log("strip", dl.LineStrips3D([points]))
