"""Log different transforms between three arrows."""

from math import pi

import dalaran as dl
from dalaran.datatypes import Angle, RotationAxisAngle

dl.init("dalaran_example_transform3d", spawn=True)

arrow = dl.Arrows3D(origins=[0, 0, 0], vectors=[0, 1, 0])

dl.log("base", arrow)

dl.log("base/translated", dl.Transform3D(translation=[1, 0, 0]))
dl.log("base/translated", arrow)

dl.log(
    "base/rotated_scaled",
    dl.Transform3D(
        rotation=RotationAxisAngle(axis=[0, 0, 1], angle=Angle(rad=pi / 4)),
        scale=2,
    ),
)
dl.log("base/rotated_scaled", arrow)
