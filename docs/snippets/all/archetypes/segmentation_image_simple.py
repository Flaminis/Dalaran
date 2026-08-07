"""Create and log a segmentation image."""

import numpy as np

import dalaran as dl

# Create a segmentation image
image = np.zeros((8, 12), dtype=np.uint8)
image[0:4, 0:6] = 1
image[4:8, 6:12] = 2

dl.init("dalaran_example_segmentation_image", spawn=True)

# Assign a label and color to each class
dl.log(
    "/",
    dl.AnnotationContext([(1, "red", (255, 0, 0)), (2, "green", (0, 255, 0))]),
    static=True,
)

dl.log("image", dl.SegmentationImage(image))
