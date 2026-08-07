"""Log a few gaussian splats."""

import dalaran as dl

dl.init("dalaran_example_gaussian_splats3d", spawn=True)

dl.log(
    "gaussians",
    dl.GaussianSplats3D(
        centers=[[0, 0, 0], [2, 0, 0], [4, 0, 0]],
        scales=[[1.0, 0.5, 0.25], [0.5, 1.0, 0.5], [0.25, 0.5, 1.0]],
        quaternions=[
            dl.Quaternion.identity(),
            dl.Quaternion(
                xyzw=[0.0, 0.0, 0.382683, 0.923880]
            ),  # 45 degrees around Z
            dl.Quaternion.identity(),
        ],
        colors=[(255, 0, 0, 128), (0, 255, 0, 200), (0, 0, 255, 255)],
        # 15 view-dependent RGB coefficients (degrees 1-3) per splat:
        sh_coefficients=[
            [[0.5, 0.0, 0.0]] * 15,
            [[0.0, 0.5, 0.0]] * 15,
            [[0.0, 0.0, 0.5]] * 15,
        ],
    ),
)
