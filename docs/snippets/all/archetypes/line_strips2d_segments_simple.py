"""Log a couple 2D line segments using 2D line strips."""

import numpy as np

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_line_segments2d", spawn=True)

dl.log(
    "segments",
    dl.LineStrips2D(np.array([[[0, 0], [2, 1]], [[4, -1], [6, 0]]])),
)

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-1, 7], y_range=[-3, 3])
    )
)
