"""Log a pinhole and a random image."""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_pinhole", spawn=True)
rng = np.random.default_rng(12345)

image = rng.uniform(0, 255, size=[3, 3, 3])
dl.log("world/image", dl.Pinhole(focal_length=3, width=3, height=3))
dl.log("world/image", dl.Image(image))
