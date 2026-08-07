"""Log a batch of 2D arrows."""

import dalaran as dl

dl.init("dalaran_example_arrow2d", spawn=True)

dl.log(
    "arrows",
    dl.Arrows2D(
        origins=[[0.25, 0.0], [0.25, 0.0], [-0.1, -0.1]],
        vectors=[[1.0, 0.0], [0.0, -1.0], [-0.7, 0.7]],
        colors=[[255, 0, 0], [0, 255, 0], [127, 0, 255]],
        labels=["right", "up", "left-down"],
        radii=0.025,
    ),
)
