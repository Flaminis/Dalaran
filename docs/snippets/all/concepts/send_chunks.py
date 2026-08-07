"""Send chunks loaded from an DLR into a recording stream."""

import sys

import dalaran as dl
import dalaran.experimental as rrx

path_to_dlr = sys.argv[1]

# NOTE: This is specifically demonstrating how to forward chunks from an DLR
# into the viewer.
# If you just want to view an DLR file, use the simpler `dl.log_file()`
# function instead:
#   dl.log_file("path/to/file.dlr", spawn=True)

reader = rrx.RrdReader(path_to_dlr)
entry = reader.recordings()[0]

dl.init(entry.application_id, recording_id=entry.recording_id, spawn=True)
rrx.send_chunks(reader.store())
