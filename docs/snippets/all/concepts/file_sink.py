"""Create and set a file sink."""

import dalaran as dl

dl.init("dalaran_example_file_sink")

dl.set_sinks(dl.FileSink("recording.dlr"))
