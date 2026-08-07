import dalaran as dl

dl.init("dalaran_example_log_to_dlr")

# Open a local file handle to stream the data into.
dl.save("/tmp/my_recording.dlr")

# Log data as usual, thereby writing it into the file.
while True:
    dl.log("/", dl.TextLog("Logging things…"))
