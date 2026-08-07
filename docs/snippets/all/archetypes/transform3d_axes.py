"""Log different transforms with visualized coordinates axes."""

import dalaran as dl

dl.init("dalaran_example_transform3d_axes", spawn=True)

dl.set_time("step", sequence=0)

# Set the axis lengths for all the transforms
dl.log("base", dl.Transform3D(), dl.TransformAxes3D(1.0))

# Now sweep out a rotation relative to the base
for deg in range(360):
    dl.set_time("step", sequence=deg)
    dl.log(
        "base/rotated",
        dl.Transform3D.from_fields(
            rotation_axis_angle=dl.RotationAxisAngle(
                axis=[1.0, 1.0, 1.0],
                degrees=deg,
            ),
        ),
        dl.TransformAxes3D(0.5),
    )
    dl.log(
        "base/rotated/translated",
        dl.Transform3D.from_fields(
            translation=[2.0, 0, 0],
        ),
        dl.TransformAxes3D(0.5),
    )
