import math

import dalaran as dl

with dl.RecordingStream(
    "dalaran_example_getting_started",
    recording_id="run-1",
    send_properties=False,
) as rec:
    rec.save("run-1.dlr")
    for t in range(10):
        rec.set_time("step", sequence=t)
        rec.log("/arm/shoulder", dl.Scalars(math.sin(t * 0.5)))
        rec.log("/arm/elbow", dl.Scalars(math.cos(t * 0.5)))
