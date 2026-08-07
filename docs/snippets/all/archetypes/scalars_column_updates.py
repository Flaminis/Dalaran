"""
Update a scalar over time, in a single operation.

This is semantically equivalent to the `scalar_row_updates` example,
albeit much faster.
"""

from __future__ import annotations

import numpy as np

import dalaran as dl

dl.init("dalaran_example_scalar_column_updates", spawn=True)

times = np.arange(0, 64)
scalars = np.sin(times / 10.0)

dl.send_columns(
    "scalars",
    indexes=[dl.TimeColumn("step", sequence=times)],
    columns=dl.Scalars.columns(scalars=scalars),
)
