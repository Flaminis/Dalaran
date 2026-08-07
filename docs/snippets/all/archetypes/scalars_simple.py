"""Log a scalar over time."""

import math

import dalaran as dl

dl.init("dalaran_example_scalar", spawn=True)

# Log the data on a timeline called "step".
for step in range(64):
    dl.set_time("step", sequence=step)
    dl.log("scalar", dl.Scalars(math.sin(step / 10.0)))
