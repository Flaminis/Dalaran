"""Logs a simple transform hierarchy with named frames."""

import dalaran as dl

dl.init("dalaran_example_transform3d_hierarchy_named_frames", spawn=True)

# Define entities with explicit coordinate frames.
dl.log(
    "sun",
    dl.Ellipsoids3D(
        half_sizes=[1, 1, 1], colors=[255, 200, 10], fill_mode="solid"
    ),
    dl.CoordinateFrame("sun_frame"),
)
dl.log(
    "planet",
    dl.Ellipsoids3D(
        half_sizes=[0.4, 0.4, 0.4], colors=[40, 80, 200], fill_mode="solid"
    ),
    dl.CoordinateFrame("planet_frame"),
)
dl.log(
    "moon",
    dl.Ellipsoids3D(
        half_sizes=[0.15, 0.15, 0.15], colors=[180, 180, 180], fill_mode="solid"
    ),
    dl.CoordinateFrame("moon_frame"),
)

# Define explicit frame relationships.
dl.log(
    "planet_transform",
    dl.Transform3D(
        translation=[6.0, 0.0, 0.0],
        child_frame="planet_frame",
        parent_frame="sun_frame",
    ),
)
dl.log(
    "moon_transform",
    dl.Transform3D(
        translation=[3.0, 0.0, 0.0],
        child_frame="moon_frame",
        parent_frame="planet_frame",
    ),
)

# Connect the viewer to the sun's coordinate frame.
# This is only needed in the absence of blueprints since a default view will
# typically be created at `/`.
dl.log("/", dl.CoordinateFrame("sun_frame"), static=True)
