"""Log a simple line strip."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_line_strip2d", spawn=True)

dl.log(
    "strip",
    dl.LineStrips2D([[[0, 0], [2, 1], [4, -1], [6, 0]]]),
)

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-1, 7], y_range=[-3, 3])
    )
)
