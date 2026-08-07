"""Log a simple 2D Box."""

import dalaran as dl

dl.init("dalaran_example_box2d", spawn=True)

dl.log("simple", dl.Boxes2D(mins=[-1, -1], sizes=[2, 2]))
