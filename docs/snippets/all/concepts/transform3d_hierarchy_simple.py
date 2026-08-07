"""Logs a simple transform hierarchy."""

import dalaran as dl

dl.init("dalaran_example_transform3d_hierarchy_simple", spawn=True)

# Log entities at their hierarchy positions.
dl.log(
    "sun",
    dl.Ellipsoids3D(
        half_sizes=[1, 1, 1], colors=[255, 200, 10], fill_mode="solid"
    ),
)
dl.log(
    "sun/planet",
    dl.Ellipsoids3D(
        half_sizes=[0.4, 0.4, 0.4], colors=[40, 80, 200], fill_mode="solid"
    ),
)
dl.log(
    "sun/planet/moon",
    dl.Ellipsoids3D(
        half_sizes=[0.15, 0.15, 0.15], colors=[180, 180, 180], fill_mode="solid"
    ),
)

# Define transforms - each describes the relationship to its parent.
dl.log(
    "sun/planet", dl.Transform3D(translation=[6.0, 0.0, 0.0])
)  # Planet 6 units from sun.
dl.log(
    "sun/planet/moon", dl.Transform3D(translation=[3.0, 0.0, 0.0])
)  # Moon 3 units from planet.
