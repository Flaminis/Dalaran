"""
Update an image over time.

See also the `image_column_updates` example, which achieves the same
thing in a single operation.
"""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_image_row_updates", spawn=True)

for t in range(20):
    dl.set_time("time", sequence=t)

    image = np.zeros((200, 300, 3), dtype=np.uint8)
    image[:, :, 2] = 255
    image[50:150, (t * 10) : (t * 10 + 100)] = (0, 255, 255)

    dl.log("image", dl.Image(image))
