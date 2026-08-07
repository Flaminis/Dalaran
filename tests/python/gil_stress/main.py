"""
Stress test for things that tend to GIL deadlock.

Logs many large recordings that contain a lot of large rows.

Usage:
```
python main.py
"""

from __future__ import annotations

import dalaran as dl

rec = dl.RecordingStream(application_id="test")

rec = dl.RecordingStream(application_id="test")
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test", make_default=True)
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test", make_thread_default=True)
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test")  # this works
dl.set_global_data_recording(rec)
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test")  # this works
dl.set_thread_local_data_recording(rec)
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test")
rec.spawn()
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test")
dl.connect_grpc(recording=rec)
rec.log("test", dl.Points3D([1, 2, 3]))

rec = dl.RecordingStream(application_id="test")
dl.memory_recording(recording=rec)
rec.log("test", dl.Points3D([1, 2, 3]))

for _ in range(3):
    rec = dl.RecordingStream(application_id="test", make_default=False, make_thread_default=False)
    mem = rec.memory_recording()
    rec.log("test", dl.Points3D([1, 2, 3]))

for _ in range(3):
    rec = dl.RecordingStream(application_id="test", make_default=False, make_thread_default=False)
    rec.log("test", dl.Points3D([1, 2, 3]))
