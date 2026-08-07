#!/usr/bin/env python3
"""Showcases how to incrementally log data belonging to the same archetype, and re-use some or all of it across frames."""

from __future__ import annotations

import argparse

from numpy.random import default_rng

import dalaran as dl

parser = argparse.ArgumentParser(description="Showcases how to incrementally log data belonging to the same archetype.")
dl.script_add_args(parser)
args = parser.parse_args()


README = """\
# Incremental Logging

This example showcases how to incrementally log data belonging to the same archetype, and re-use some or all of it across frames.

It was logged with the following code:
```python
# Only log colors and radii once.
# Logging as static would also work (i.e. `static=True`).
dl.set_time("frame_nr", sequence=0)
dl.log("points", dl.Points3D.from_fields(colors=0xFF0000FF, radii=0.1))

rng = default_rng(12345)

# Then log only the points themselves each frame.
#
# They will automatically re-use the colors and radii logged at the beginning.
for i in range(10):
    dl.set_time("frame_nr", sequence=i)
    dl.log("points", dl.Points3D.from_fields(positions=rng.uniform(-5, 5, size=[10, 3])))
```

Move the time cursor around, and notice how the colors and radii from frame 0 are still picked up by later frames, while the points themselves keep changing every frame.
"""

# ---

dl.script_setup(args, "dalaran_example_incremental_logging")

dl.log("readme", dl.TextDocument(README, media_type=dl.MediaType.MARKDOWN), static=True)

# Only log colors and radii once.
# Logging as static would also work (i.e. `static=True`).
dl.set_time("frame_nr", sequence=0)
dl.log("points", dl.Points3D.from_fields(colors=0xFF0000FF, radii=0.1))

rng = default_rng(12345)

# Then log only the points themselves each frame.
#
# They will automatically re-use the colors and radii logged at the beginning.
for i in range(10):
    dl.set_time("frame_nr", sequence=i)
    dl.log("points", dl.Points3D.from_fields(positions=rng.uniform(-5, 5, size=[10, 3])))

dl.script_teardown(args)
