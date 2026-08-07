"""
Update a set of vectors over time.

See also the `arrows3d_column_updates` example, which achieves the same
thing in a single operation.
"""

import numpy as np

import dalaran as dl

dl.init("dalaran_example_arrows3d_row_updates", spawn=True)

# Prepare a fixed sequence of arrows over 5 timesteps.
# Origins stay constant, vectors change magnitude and direction, and each
# timestep has a unique color.
times = np.arange(10, 15, 1.0)

# At each time step, all arrows maintain their origin.
origins = np.linspace((-1, -1, 0), (1, 1, 0), 5)
vectors = [np.linspace((-1, -1, 0), (1, 1, i), 5) for i in range(5)]


# At each timestep, all arrows share the same but changing color.
colors = [0xFF0000FF, 0x00FF00FF, 0x0000FFFF, 0xFFFF00FF, 0x00FFFFFF]

for i in range(5):
    dl.set_time("time", duration=10 + i)
    dl.log(
        "arrows",
        dl.Arrows3D(vectors=vectors[i], origins=origins, colors=colors[i]),
    )
