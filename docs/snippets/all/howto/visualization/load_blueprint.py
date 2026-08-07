"""
Query and display the first 10 rows of a recording in a dataframe view.

The blueprint is being loaded from an existing blueprint recording file.
"""

# python dataframe_view_query_external.py /tmp/dna.dlr /tmp/dna.dbl

import sys

import dalaran as dl

path_to_dlr = sys.argv[1]
path_to_dbl = sys.argv[2]

dl.init("dalaran_example_dataframe_view_query_external", spawn=True)

dl.log_file_from_path(path_to_dlr)
dl.log_file_from_path(path_to_dbl)
