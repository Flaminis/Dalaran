"""
Log a simple 3D mesh with several instance pose transforms.

This instantiate the mesh several times and will not
affect its children. This is known as mesh instancing.
"""

import dalaran as dl

dl.init("dalaran_example_mesh3d_instancing", spawn=True)
dl.set_time("frame", sequence=0)

dl.log(
    "shape",
    dl.Mesh3D(
        vertex_positions=[[1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]],
        triangle_indices=[[0, 2, 1], [0, 3, 1], [0, 3, 2], [1, 3, 2]],
        vertex_colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]],
    ),
)
# This box will not be affected by its parent's instance poses!
dl.log(
    "shape/box",
    dl.Boxes3D(half_sizes=[[5.0, 5.0, 5.0]]),
)

for i in range(100):
    dl.set_time("frame", sequence=i)
    dl.log(
        "shape",
        dl.InstancePoses3D(
            translations=[[2, 0, 0], [0, 2, 0], [0, -2, 0], [-2, 0, 0]],
            rotation_axis_angles=dl.RotationAxisAngle(
                [0, 0, 1], dl.Angle(deg=i * 2)
            ),
        ),
    )
