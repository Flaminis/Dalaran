"""Demonstrates how to programmatically re-use a blueprint stored in a file."""

import sys

import dalaran as dl

path_to_dbl = sys.argv[1]

dl.init("dalaran_example_reuse_blueprint_file", spawn=True)
dl.log_file_from_path(path_to_dbl)

# … log some data as usual …
