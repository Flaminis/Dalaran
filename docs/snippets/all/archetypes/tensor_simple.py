"""Create and log a tensor."""

import numpy as np

import dalaran as dl

tensor = np.random.randint(
    0, 256, (8, 6, 3, 5), dtype=np.uint8
)  # 4-dimensional tensor

dl.init("dalaran_example_tensor", spawn=True)

# Log the tensor, assigning names to each dimension
dl.log(
    "tensor",
    dl.Tensor(tensor, dim_names=("width", "height", "channel", "batch")),
)
