"""
Update a transform over time.

See also the `transform3d_column_updates` example, which achieves the same
thing in a single operation.
"""

import math

import dalaran as dl


def truncated_radians(deg: float) -> float:
    return float(int(math.radians(deg) * 1000.0)) / 1000.0


dl.init("dalaran_example_transform3d_row_updates", spawn=True)

dl.set_time("tick", sequence=0)
dl.log(
    "box",
    dl.Boxes3D(
        half_sizes=[4.0, 2.0, 1.0], fill_mode=dl.components.FillMode.Solid
    ),
    dl.TransformAxes3D(10.0),
)

for t in range(100):
    dl.set_time("tick", sequence=t + 1)
    dl.log(
        "box",
        dl.Transform3D(
            translation=[0, 0, t / 10.0],
            rotation_axis_angle=dl.RotationAxisAngle(
                axis=[0.0, 1.0, 0.0], radians=truncated_radians(t * 4)
            ),
        ),
    )
