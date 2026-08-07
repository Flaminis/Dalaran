"""Log a batch of 2D line strips."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_line_strip2d_batch", spawn=True)

dl.log(
    "strips",
    dl.LineStrips2D(
        [
            [[0, 0], [2, 1], [4, -1], [6, 0]],
            [[0, 3], [1, 4], [2, 2], [3, 4], [4, 2], [5, 4], [6, 3]],
        ],
        colors=[[255, 0, 0], [0, 255, 0]],
        radii=[0.025, 0.005],
        labels=["one strip here", "and one strip there"],
    ),
)

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-1, 7], y_range=[-3, 6])
    )
)
