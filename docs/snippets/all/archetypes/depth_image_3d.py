"""Create and log a depth image and pinhole camera."""

import numpy as np

import dalaran as dl

depth_image = 65535 * np.ones((200, 300), dtype=np.uint16)
depth_image[50:150, 50:150] = 20000
depth_image[130:180, 100:280] = 45000

dl.init("dalaran_example_depth_image_3d", spawn=True)

# If we log a pinhole camera model, the depth gets automatically
# back-projected to 3D
dl.log(
    "world/camera",
    dl.Pinhole(
        width=depth_image.shape[1],
        height=depth_image.shape[0],
        focal_length=200,
    ),
)

# Log the tensor.
dl.log(
    "world/camera/depth",
    dl.DepthImage(depth_image, meter=10_000.0, colormap="viridis"),
)
