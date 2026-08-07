"""Logs a point cloud and a perspective camera looking at it."""

import dalaran as dl

dl.init("dalaran_example_pinhole_perspective", spawn=True)

dl.log(
    "world/cam",
    dl.Pinhole(
        fov_y=0.7853982,
        aspect_ratio=1.7777778,
        camera_xyz=dl.ViewCoordinates.RUB,
        image_plane_distance=0.1,
        color=[255, 128, 0],
        line_width=0.003,
    ),
)

dl.log(
    "world/points",
    dl.Points3D(
        [(0.0, 0.0, -0.5), (0.1, 0.1, -0.5), (-0.1, -0.1, -0.5)], radii=0.025
    ),
)
