"""Create a new dataset from a subset of segments of an existing dataset."""

# region: setup
from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
from datafusion import col, lit
from datafusion import functions as F

import dalaran as dl

sample_5_path = (
    Path(__file__).parents[4] / "tests" / "assets" / "dlr" / "sample_5"
)

server = dl.server.Server(datasets={"sample_dataset": sample_5_path})
CATALOG_URL = server.url()
client = dl.catalog.CatalogClient(CATALOG_URL)
source_dataset = client.get_dataset(name="sample_dataset")
# endregion: setup


# region: create_sub_dataset
def create_sub_dataset(
    client: dl.catalog.CatalogClient,
    source: dl.catalog.DatasetEntry,
    name: str,
    segment_ids: list[str],
) -> dl.catalog.DatasetEntry:
    """Create a new dataset with a subset of segments from another dataset."""

    # Look up the storage URLs of the selected segments.
    selected = pa.table(
        source
        .segment_table()
        .filter(
            F.in_list(col("dalaran_segment_id"), [lit(s) for s in segment_ids])
        )
        .select("dalaran_storage_urls", "dalaran_layer_names")
    )

    sub_dataset = client.create_dataset(name)

    # Flatten the per-segment lists into the (url, layer) pairs to register.
    uris = pc.list_flatten(selected.column("dalaran_storage_urls")).to_pylist()
    layers = pc.list_flatten(selected.column("dalaran_layer_names")).to_pylist()

    if uris:
        sub_dataset.register(uris, layer_name=layers).wait()

    return sub_dataset


# endregion: create_sub_dataset

# region: select_segments
# View available segments
print("Available segments:")
print(
    source_dataset
    .segment_table()
    .select("dalaran_segment_id")
    .sort("dalaran_segment_id")
)

# Select a subset — here we pick the first 3 segments.
all_segment_ids = source_dataset.segment_ids()
subset_ids = all_segment_ids[:3]
# endregion: select_segments

# region: create
sub_dataset = create_sub_dataset(
    client, source_dataset, "my_experiment", subset_ids
)
# endregion: create

# region: verify
print("\nSub-dataset segments:")
print(
    sub_dataset
    .segment_table()
    .select("dalaran_segment_id", "dalaran_layer_names")
    .sort("dalaran_segment_id")
)

print("\nSub-dataset storage URLs:")
print(
    sub_dataset
    .segment_table()
    .select("dalaran_segment_id", "dalaran_layer_names", "dalaran_storage_urls")
    .sort("dalaran_segment_id")
)
# endregion: verify

# region: cleanup
# When done experimenting, delete the sub-dataset.
# This only removes the dataset entry — the underlying DLR storage is not
# affected.
sub_dataset.delete()
# endregion: cleanup
