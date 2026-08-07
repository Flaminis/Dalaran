"""Logs a transform hierarchy using named transform frame relationships."""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_transform3d_hierarchy_frames", spawn=True)

dl.set_time("sim_time", duration=0)

# Planetary motion is typically in the XY plane.
dl.log("/", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

# Setup spheres, all are in the center of their own space:
dl.log(
    "sun",
    dl.Ellipsoids3D(
        centers=[0, 0, 0],
        half_sizes=[1, 1, 1],
        colors=[255, 200, 10],
        fill_mode="solid",
    ),
    dl.CoordinateFrame("sun_frame"),
)

dl.log(
    "planet",
    dl.Ellipsoids3D(
        centers=[0, 0, 0],
        half_sizes=[0.4, 0.4, 0.4],
        colors=[40, 80, 200],
        fill_mode="solid",
    ),
    dl.CoordinateFrame("planet_frame"),
)

dl.log(
    "moon",
    dl.Ellipsoids3D(
        centers=[0, 0, 0],
        half_sizes=[0.15, 0.15, 0.15],
        colors=[180, 180, 180],
        fill_mode="solid",
    ),
    dl.CoordinateFrame("moon_frame"),
)

# The viewer automatically creates a 3D view at `/`. To connect it to our
# transform hierarchy, we set its coordinate frame to `sun_frame` as well.
# Alternatively, we could also set a blueprint that makes `/sun` the space
# origin.
dl.log("/", dl.CoordinateFrame("sun_frame"))

# Draw fixed paths where the planet & moon move.
d_planet = 6.0
d_moon = 3.0
angles = np.arange(0.0, 1.01, 0.01) * np.pi * 2
circle = np.array(
    [np.sin(angles), np.cos(angles), angles * 0.0], dtype=np.float32
).transpose()
dl.log(
    "planet_path",
    dl.LineStrips3D(circle * d_planet),
    dl.CoordinateFrame("sun_frame"),
)
dl.log(
    "moon_path",
    dl.LineStrips3D(circle * d_moon),
    dl.CoordinateFrame("planet_frame"),
)

# Movement via transforms.
for i in range(6 * 120):
    time = i / 120.0
    dl.set_time("sim_time", duration=time)
    r_moon = time * 5.0
    r_planet = time * 2.0

    dl.log(
        "planet_transforms",
        dl.Transform3D(
            translation=[
                np.sin(r_planet) * d_planet,
                np.cos(r_planet) * d_planet,
                0.0,
            ],
            rotation=dl.RotationAxisAngle(axis=(1, 0, 0), degrees=20),
            child_frame="planet_frame",
            parent_frame="sun_frame",
        ),
    )
    dl.log(
        "moon_transforms",
        dl.Transform3D(
            translation=[np.cos(r_moon) * d_moon, np.sin(r_moon) * d_moon, 0.0],
            relation=dl.TransformRelation.ChildFromParent,
            child_frame="moon_frame",
            parent_frame="planet_frame",
        ),
    )
