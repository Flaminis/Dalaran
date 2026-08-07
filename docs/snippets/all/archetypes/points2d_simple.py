"""Log some very simple points."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_points2d", spawn=True)

dl.log("points", dl.Points2D([[0, 0], [1, 1]]))

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-1, 2], y_range=[-1, 2])
    )
)
