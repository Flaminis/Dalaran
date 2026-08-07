"""Log a simple 2D ellipse."""

import dalaran as dl

dl.init("dalaran_example_ellipses2d", spawn=True)

dl.log("simple", dl.Ellipses2D(half_sizes=[(2.0, 1.0)], centers=[(0.0, 0.0)]))
