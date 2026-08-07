"""
Query and display the first 10 rows of a recording in a dataframe view.

The blueprint is being loaded from an existing blueprint recording file.
"""

# python dataframe_view_query_external.py /tmp/dna.rrd /tmp/dna.rbl

import sys

import dalaran as dl

path_to_rrd = sys.argv[1]
path_to_rbl = sys.argv[2]

dl.init("dalaran_example_dataframe_view_query_external", spawn=True)

dl.log_file_from_path(path_to_rrd)
dl.log_file_from_path(path_to_rbl)
