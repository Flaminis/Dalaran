"""Use a blueprint to customize a Spatial3DView."""

from numpy.random import default_rng

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_spatial_3d", spawn=True)

# Create some random points.
rng = default_rng(12345)
positions = rng.uniform(-5, 5, size=[50, 3])
colors = rng.uniform(0, 255, size=[50, 3])
radii = rng.uniform(0.1, 0.5, size=[50])

dl.log("points", dl.Points3D(positions, colors=colors, radii=radii))
dl.log("box", dl.Boxes3D(half_sizes=[5, 5, 5], colors=0))

# Create a Spatial3D view to display the points.
blueprint = dlb.Blueprint(
    dlb.Spatial3DView(
        origin="/",
        name="3D Scene",
        # Set the background color to light blue.
        background=[100, 149, 237],
        # Configure the eye controls.
        eye_controls=dlb.EyeControls3D(
            position=(0.0, 0.0, 2.0),
            look_target=(0.0, 2.0, 0.0),
            eye_up=(-1.0, 0.0, 0.0),
            spin_speed=0.2,
            kind=dlb.Eye3DKind.FirstPerson,
            speed=20.0,
        ),
        # Configure the line grid.
        line_grid=dlb.LineGrid3D(
            # The grid is enabled by default, but you can hide it.
            visible=True,
            spacing=0.1,  # Makes the grid more fine-grained.
            # By default, the plane is inferred from view coordinates setup,
            # but you can set arbitrary planes.
            plane=dl.components.Plane3D.XY.with_distance(-5.0),
            stroke_width=2.0,  # Makes the grid lines twice as thick as usual.
            color=[
                255,
                255,
                255,
                128,
            ],  # Colors the grid a half-transparent white.
        ),
        spatial_information=dlb.SpatialInformation(
            target_frame="tf#/",
            show_axes=True,
            show_bounding_box=True,
        ),
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
