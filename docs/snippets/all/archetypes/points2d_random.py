"""Log some random points with color and radii."""

from numpy.random import default_rng

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_points2d_random", spawn=True)
rng = default_rng(12345)

positions = rng.uniform(-3, 3, size=[10, 2])
colors = rng.uniform(0, 255, size=[10, 4])
radii = rng.uniform(0, 1, size=[10])

dl.log("random", dl.Points2D(positions, colors=colors, radii=radii))

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-4, 4], y_range=[-4, 4])
    )
)
