"""Log a simple colored triangle."""

import dalaran as dl

dl.init("dalaran_example_mesh3d_indexed", spawn=True)

dl.log(
    "triangle",
    dl.Mesh3D(
        vertex_positions=[[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        vertex_normals=[0.0, 0.0, 1.0],
        vertex_colors=[[0, 0, 255], [0, 255, 0], [255, 0, 0]],
        triangle_indices=[2, 1, 0],
    ),
)
