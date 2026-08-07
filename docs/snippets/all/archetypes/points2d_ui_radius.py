"""Log some points with ui points & scene unit radii."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_points2d_ui_radius", spawn=True)

# Two blue points with scene unit radii of 0.1 and 0.3.
dl.log(
    "scene_units",
    dl.Points2D(
        [[0, 0], [0, 1]],
        # By default, radii are interpreted as world-space units.
        radii=[0.1, 0.3],
        colors=[0, 0, 255],
    ),
)

# Two red points with ui point radii of 40 and 60.
# UI points are independent of zooming in Views, but are sensitive to the
# application UI scaling.
# For 100% ui scaling, UI points are equal to pixels.
dl.log(
    "ui_points",
    dl.Points2D(
        [[1, 0], [1, 1]],
        # dl.Radius.ui_points produces radii that the viewer interprets
        # as given in ui points.
        radii=dl.Radius.ui_points([40.0, 60.0]),
        colors=[255, 0, 0],
    ),
)

# Set view bounds:
dl.send_blueprint(
    dlb.Spatial2DView(
        visual_bounds=dlb.VisualBounds2D(x_range=[-1, 2], y_range=[-1, 2])
    )
)
