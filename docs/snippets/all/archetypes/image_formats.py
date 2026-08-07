"""Create and log an image with various formats."""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_image_formats", spawn=True)

# Simple gradient image, logged in different formats.
image = np.array(
    [[[x, min(255, x + y), y] for x in range(256)] for y in range(256)],
    dtype=np.uint8,
)
dl.log("image_rgb", dl.Image(image))
dl.log(
    "image_green_only", dl.Image(image[:, :, 1], color_model="l")
)  # Luminance only
dl.log("image_bgr", dl.Image(image[:, :, ::-1], color_model="bgr"))  # BGR

# New image with Separate Y/U/V planes with 4:2:2 chroma downsampling
y = bytes([128 for y in range(256) for x in range(256)])
u = bytes([
    x * 2 for y in range(256) for x in range(128)
])  # Half horizontal resolution for chroma.
v = bytes([y for y in range(256) for x in range(128)])
dl.log(
    "image_yuv422",
    dl.Image(
        bytes=y + u + v,
        width=256,
        height=256,
        pixel_format=dl.PixelFormat.Y_U_V16_FullRange,
    ),
)
