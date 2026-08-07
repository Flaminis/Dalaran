"""Log different data on different timelines."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_different_data_per_timeline", spawn=True)

dl.set_time("blue timeline", sequence=0)
dl.set_time("red timeline", duration=0.0)
dl.log("points", dl.Points2D([[0, 0], [1, 1]], radii=dl.Radius.ui_points(10.0)))

# Log a red color on one timeline.
dl.reset_time()  # Clears all set timeline info.
dl.set_time("red timeline", duration=1.0)
dl.log("points", dl.Points2D.from_fields(colors=[255, 0, 0]))

# And a blue color on the other.
dl.reset_time()  # Clears all set timeline info.
dl.set_time("blue timeline", sequence=1)
dl.log("points", dl.Points2D.from_fields(colors=[0, 0, 255]))


# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-1, 2], y_range=[-1, 2])
    )
)
