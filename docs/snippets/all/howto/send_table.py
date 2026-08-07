"""Sets the recording properties."""

import pyarrow as pa

from dalaran.experimental import ViewerClient

client = ViewerClient.connect(url="dalaran+http://127.0.0.1:9876/proxy")
client.send_table(
    "Hello from Python",
    pa.RecordBatch.from_pydict({
        "id": [1, 2, 3],
        "url": [
            "https://www.dalaran.dev",
            "https://github.com/Flaminis/Dalaran",
            "https://crates.io/crates/dalaran",
        ],
    }),
)
