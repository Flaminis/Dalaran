"""Use `AnyBatchValue` and `send_column` to send a column of custom data."""

from __future__ import annotations

import numpy as np

import dalaran as dl

dl.init("dalaran_example_any_batch_value_column_updates", spawn=True)

N = 64
timestamps = np.arange(0, N)
one_per_timestamp = np.sin(timestamps / 10.0)
ten_per_timestamp = np.cos(np.arange(0, N * 10) / 100.0)

maybe_single_batch = dl.AnyBatchValue.column(
    "custom_component_single", one_per_timestamp
)
if maybe_single_batch is not None:
    single_batch = maybe_single_batch
else:
    raise ValueError("Failed to create AnyBatchValue for single_per_timestamp")

maybe_multi_batch = dl.AnyBatchValue.column(
    "custom_component_multi", ten_per_timestamp
)
if maybe_multi_batch is not None:
    multi_batch = maybe_multi_batch.partition([10] * N)
else:
    raise ValueError(
        "Failed to create AnyBatchValue for multiple_per_timestamp"
    )


dl.send_columns(
    "/",
    indexes=[dl.TimeColumn("step", sequence=timestamps)],
    columns=[
        # log one value per timestamp
        single_batch,
        # log ten values per timestamp
        multi_batch,
    ],
)
