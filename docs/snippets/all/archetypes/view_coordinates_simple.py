"""Set the default orientation for a 3D view."""

import dalaran as dl

dl.init("dalaran_example_view_coordinates", spawn=True)

dl.log(
    "world", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True
)  # Set the 3D view's up direction
dl.log(
    "world/xyz",
    dl.Arrows3D(
        vectors=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
    ),
)
