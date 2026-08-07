"""Query and display the first 10 rows of a recording."""

import atexit
import math
import tempfile
from pathlib import Path

from datafusion import col

import dalaran as dl

# a cross-platform way to generate a dlr path, cleaned up when the process exits
_tmp_dir = tempfile.TemporaryDirectory()
atexit.register(_tmp_dir.cleanup)
DLR_PATH = str(Path(_tmp_dir.name) / "query_example.dlr")

# region: setup
# create some data
times = list(range(64))
scalars = [math.sin(t / 10.0) for t in times]

# log the data to a temporary recording
with dl.RecordingStream("dalaran_example_dataframe_query") as rec:
    rec.save(DLR_PATH)
    rec.send_columns(
        "/data",
        indexes=[dl.TimeColumn("step", sequence=times)],
        columns=dl.Scalars.columns(scalars=scalars),
    )
# endregion: setup


# region: query
# load the demo recording in a temporary catalog
with dl.server.Server(datasets={"dataset": [DLR_PATH]}) as server:
    # obtain a dataset from the catalog
    dataset = server.client().get_dataset("dataset")

    # (optional) filter interesting data
    dataset_view = dataset.filter_contents("/data")

    # obtain a DataFusion dataframe
    df = dataset_view.reader(index="step")

    # (optional) filter rows using DataFusion expressions
    df = df.filter(col("/data:Scalars:scalars")[0] > 0.95)

    # execute the query
    print(df)  # or convert to Pandas, Polars, PyArrow, etc.
# endregion: query
