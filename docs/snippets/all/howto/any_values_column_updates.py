"""
Update custom user-defined values over time, in a single operation.

This is semantically equivalent to the `any_values_row_updates` example,
albeit much faster.
"""

from __future__ import annotations

import numpy as np

import dalaran as dl

dl.init("dalaran_example_any_values_column_updates", spawn=True)

timestamps = np.arange(0, 64)

dl.send_columns(
    "/",
    indexes=[dl.TimeColumn("step", sequence=timestamps)],
    columns=dl.AnyValues.columns(
        sin=np.sin(timestamps / 10.0), cos=np.cos(timestamps / 10.0)
    ),
)
