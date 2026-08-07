"""Load an MCAP file using the Python SDK."""

import sys

import dalaran as dl

path_to_mcap = sys.argv[1]

# Initialize the SDK and give our recording a unique name
dl.init("dalaran_example_load_mcap", spawn=True)

# Load the MCAP file
dl.log_file_from_path(path_to_mcap)
recording = dl.get_data_recording()
assert recording is not None
recording.flush()
