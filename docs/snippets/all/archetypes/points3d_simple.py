"""Log some very simple points."""

import dalaran as dl

dl.init("dalaran_example_points3d", spawn=True)

dl.log("points", dl.Points3D([[0, 0, 0], [1, 1, 1]]))
