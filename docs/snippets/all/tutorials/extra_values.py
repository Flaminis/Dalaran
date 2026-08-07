"""Log extra values with a `Points2D`."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_extra_values", spawn=True)

dl.log(
    "extra_values",
    dl.Points2D([[-1, -1], [-1, 1], [1, -1], [1, 1]]),
    dl.AnyValues(
        confidence=[0.3, 0.4, 0.5, 0.6],
    ),
)

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(
            x_range=[-1.5, 1.5], y_range=[-1.5, 1.5]
        )
    )
)
