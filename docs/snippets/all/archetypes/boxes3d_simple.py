"""Log a single 3D Box."""

import dalaran as dl

dl.init("dalaran_example_box3d", spawn=True)

dl.log("simple", dl.Boxes3D(half_sizes=[2.0, 2.0, 1.0]))
