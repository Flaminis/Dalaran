"""
Update an image over time, in a single operation.

This is semantically equivalent to the `image_row_updates` example,
albeit much faster.
"""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_image_column_updates", spawn=True)

# Timeline on which the images are distributed.
times = np.arange(0, 20)

# Create a batch of images with a moving rectangle.
width, height = 300, 200
images = np.zeros((len(times), height, width, 3), dtype=np.uint8)
images[:, :, :, 2] = 255
for t in times:
    images[t, 50:150, (t * 10) : (t * 10 + 100), 1] = 255

# Log the ImageFormat and indicator once, as static.
format = dl.components.ImageFormat(
    width=width, height=height, color_model="RGB", channel_datatype="U8"
)
dl.log("images", dl.Image.from_fields(format=format), static=True)

# Send all images at once.
dl.send_columns(
    "images",
    indexes=[dl.TimeColumn("step", sequence=times)],
    # Reshape the images so `Image` can tell that this is several blobs.
    #
    # Note that the `Image` consumes arrays of bytes, so we should ensure
    # that we take a uint8 view of it. This way, this also works when
    # working with datatypes other than `U8`.
    columns=dl.Image.columns(
        buffer=images.view(np.uint8).reshape(len(times), -1)
    ),
)
