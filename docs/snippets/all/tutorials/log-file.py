import sys

import dalaran as dl

dl.init("dalaran_example_log_file", spawn=True)

dl.log_file_from_path(sys.argv[1])
