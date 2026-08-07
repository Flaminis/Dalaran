"""
Shows how to configure micro-batching directly from code.

Check out <https://dalaran.dev/docs/reference/sdk/micro-batching> for more info.
"""

from datetime import timedelta

import dalaran as dl

# Equivalent to configuring the following environment:
# * DALARAN_FLUSH_NUM_BYTES=<+inf>
# * DALARAN_FLUSH_NUM_ROWS=10
# * DALARAN_FLUSH_TICK_SECS=10
config = dl.ChunkBatcherConfig(
    flush_num_bytes=2**63,
    flush_num_rows=10,
    flush_tick=timedelta(seconds=10),
)

rec = dl.RecordingStream("dalaran_example_micro_batching", batcher_config=config)
rec.spawn()

# These 10 log calls are guaranteed be batched together, and end up in the
# same chunk.
for i in range(10):
    rec.log("logs", dl.TextLog(f"log #{i}"))
