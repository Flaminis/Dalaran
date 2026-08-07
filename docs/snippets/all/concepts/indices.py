"""Set different types of indices."""

from datetime import datetime

import numpy as np

import dalaran as dl

dl.init("dalaran_example_different_indices", spawn=True)

dl.set_time("frame_nr", sequence=42)
dl.set_time("elapsed", duration=12)  # elapsed seconds
dl.set_time("time", timestamp=1_741_017_564)  # Seconds since unix epoch
dl.set_time("time", timestamp=datetime.fromisoformat("2025-03-03T15:59:24"))
dl.set_time(
    "precise_time", timestamp=np.datetime64(1_741_017_564_987_654_000, "ns")
)  # Nanoseconds since unix epoch

# All following logged data will be timestamped with the above times:
dl.log("points", dl.Points2D([[0, 0], [1, 1]]))
