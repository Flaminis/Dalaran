"""Create and log an image."""

import numpy as np

import dalaran as dl

# Create an image with numpy
image = np.zeros((200, 300, 3), dtype=np.uint8)
image[:, :, 0] = 255
image[50:150, 50:150] = (0, 255, 0)

dl.init("dalaran_example_image", spawn=True)

dl.log("image", dl.Image(image))
