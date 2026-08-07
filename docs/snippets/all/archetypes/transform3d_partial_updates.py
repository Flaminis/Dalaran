"""Update specific properties of a transform over time."""

import math

import dalaran as dl


def truncated_radians(deg: float) -> float:
    return float(int(math.radians(deg) * 1000.0)) / 1000.0


dl.init("dalaran_example_transform3d_partial_updates", spawn=True)

# Set up a 3D box.
dl.log(
    "box",
    dl.Boxes3D(
        half_sizes=[4.0, 2.0, 1.0], fill_mode=dl.components.FillMode.Solid
    ),
)

# Update only the rotation of the box.
for deg in range(46):
    rad = truncated_radians(deg * 4)
    dl.log(
        "box",
        dl.Transform3D.from_fields(
            rotation_axis_angle=dl.RotationAxisAngle(
                axis=[0.0, 1.0, 0.0], radians=rad
            ),
        ),
    )

# Update only the position of the box.
for t in range(51):
    dl.log(
        "box",
        dl.Transform3D.from_fields(translation=[0, 0, t / 10.0]),
    )

# Update only the rotation of the box.
for deg in range(46):
    rad = truncated_radians((deg + 45) * 4)
    dl.log(
        "box",
        dl.Transform3D.from_fields(
            rotation_axis_angle=dl.RotationAxisAngle(
                axis=[0.0, 1.0, 0.0], radians=rad
            ),
        ),
    )

# Clear all of the box's attributes.
dl.log(
    "box",
    dl.Transform3D.from_fields(clear_unset=True),
)
