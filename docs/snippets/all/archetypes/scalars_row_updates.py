"""
Update a scalar over time.

See also the `scalar_column_updates` example, which achieves the same
thing in a single operation.
"""

from __future__ import annotations

import math

import dalaran as dl

dl.init("dalaran_example_scalar_row_updates", spawn=True)

for step in range(64):
    dl.set_time("step", sequence=step)
    dl.log("scalars", dl.Scalars(math.sin(step / 10.0)))
