"""Log a segmentation image with annotations."""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_annotation_context_segmentation", spawn=True)

# Create a simple segmentation image
image = np.zeros((200, 300), dtype=np.uint8)
image[50:100, 50:120] = 1
image[100:180, 130:280] = 2

# Log an annotation context to assign a label and color to each class
dl.log(
    "segmentation",
    dl.AnnotationContext([(1, "red", (255, 0, 0)), (2, "green", (0, 255, 0))]),
    static=True,
)

dl.log("segmentation/image", dl.SegmentationImage(image))
