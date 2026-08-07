from __future__ import annotations

from typing import TYPE_CHECKING

import dalaran as dl
import pyarrow as pa
import pytest
from inline_snapshot import snapshot as inline_snapshot

if TYPE_CHECKING:
    from pathlib import Path


def test_dataset_basics(complex_dataset_prefix: Path) -> None:
    with dl.server.Server() as server:
        client = server.client()

        ds = client.create_dataset("basic_dataset")

        ds.register_prefix(complex_dataset_prefix.as_uri())

        partition_df = ds.segment_table()

        assert partition_df.schema().to_string(show_field_metadata=False) == inline_snapshot("""\
dalaran_segment_id: string not null
dalaran_layer_names: list<item: string not null> not null
  child 0, item: string not null
dalaran_storage_urls: list<item: string not null> not null
  child 0, item: string not null
dalaran_last_updated_at: timestamp[ns] not null
dalaran_num_chunks: uint64 not null
dalaran_size_bytes: uint64 not null
property:RecordingInfo:start_time: list<item: int64>
  child 0, item: int64
timeline:end: timestamp[ns]
timeline:start: timestamp[ns]
-- schema metadata --
sorbet:version: '0.1.3'\
""")

        assert str(
            partition_df.drop(
                "dalaran_storage_urls",
                "dalaran_last_updated_at",
                "property:RecordingInfo:start_time",
                "dalaran_size_bytes",
            ).sort("dalaran_segment_id")
        ) == inline_snapshot("""\
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ METADATA:                                                                                                                            │
│ * version: 0.1.3                                                                                                                     │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ ┌─────────────────────┬────────────────────────────────────┬───────────────────────┬───────────────────────┬───────────────────────┐ │
│ │ dalaran_segment_id    ┆ dalaran_layer_names                  ┆ dalaran_num_chunks      ┆ timeline:end          ┆ timeline:start        │ │
│ │ ---                 ┆ ---                                ┆ ---                   ┆ ---                   ┆ ---                   │ │
│ │ type: non-null Utf8 ┆ type: non-null List(non-null Utf8) ┆ type: non-null UInt64 ┆ type: Timestamp(ns)   ┆ type: Timestamp(ns)   │ │
│ │                     ┆                                    ┆                       ┆ index: timeline       ┆ index: timeline       │ │
│ │                     ┆                                    ┆                       ┆ index_kind: timestamp ┆ index_kind: timestamp │ │
│ │                     ┆                                    ┆                       ┆ index_marker: end     ┆ index_marker: start   │ │
│ │                     ┆                                    ┆                       ┆ kind: index           ┆ kind: index           │ │
│ ╞═════════════════════╪════════════════════════════════════╪═══════════════════════╪═══════════════════════╪═══════════════════════╡ │
│ │ complex_recording_0 ┆ [base]                             ┆ 3                     ┆ 2000-01-01T00:00:02   ┆ 2000-01-01T00:00:00   │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ complex_recording_1 ┆ [base]                             ┆ 3                     ┆ 2000-01-01T00:00:03   ┆ 2000-01-01T00:00:01   │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ complex_recording_2 ┆ [base]                             ┆ 3                     ┆ 2000-01-01T00:00:04   ┆ 2000-01-01T00:00:02   │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ complex_recording_3 ┆ [base]                             ┆ 3                     ┆ 2000-01-01T00:00:05   ┆ 2000-01-01T00:00:03   │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ complex_recording_4 ┆ [base]                             ┆ 3                     ┆ 2000-01-01T00:00:06   ┆ 2000-01-01T00:00:04   │ │
│ └─────────────────────┴────────────────────────────────────┴───────────────────────┴───────────────────────┴───────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘\
""")


def test_dataset_schema(complex_dataset_prefix: Path) -> None:
    with dl.server.Server() as server:
        client = server.client()
        ds = client.create_dataset("complex_dataset")
        ds.register_prefix(complex_dataset_prefix.as_uri())

        assert str(ds.schema()) == inline_snapshot("""\
Index(timeline:timeline)
Column name: /points:Points2D:colors
	Entity path: /points
	Archetype: dalaran.archetypes.Points2D
	Component type: dalaran.components.Color
	Component: Points2D:colors
Column name: /points:Points2D:positions
	Entity path: /points
	Archetype: dalaran.archetypes.Points2D
	Component type: dalaran.components.Position2D
	Component: Points2D:positions
Column name: /text:TextLog:text
	Entity path: /text
	Archetype: dalaran.archetypes.TextLog
	Component type: dalaran.components.Text
	Component: TextLog:text
Column name: property:RecordingInfo:start_time
	Entity path: /__properties
	Archetype: dalaran.archetypes.RecordingInfo
	Component type: dalaran.components.Timestamp
	Component: RecordingInfo:start_time
	Static: true\
""")


def test_dataset_metadata(complex_dataset_prefix: Path, tmp_path: Path) -> None:
    with dl.server.Server() as server:
        client = server.client()

        ds = client.create_dataset("basic_dataset")
        ds.register_prefix(complex_dataset_prefix.as_uri())

        # TODO(jleibs): Consider attaching this metadata table directly to the dataset
        # and automatically joining it by default
        meta = client.create_table(
            "basic_dataset_metadata",
            pa.schema([
                ("dalaran_segment_id", pa.string()),
                ("success", pa.bool_()),
            ]),
            tmp_path.as_uri(),
        )

        meta.append(
            dalaran_segment_id=["complex_recording_0", "complex_recording_1", "complex_recording_4"],
            success=[True, False, True],
        )

        assert (str(meta.reader())) == inline_snapshot("""\
┌─────────────────────────────────────────┐
│ METADATA:                               │
│ * version: 0.1.3                        │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ ┌─────────────────────┬───────────────┐ │
│ │ dalaran_segment_id    ┆ success       │ │
│ │ ---                 ┆ ---           │ │
│ │ type: Utf8          ┆ type: Boolean │ │
│ ╞═════════════════════╪═══════════════╡ │
│ │ complex_recording_0 ┆ true          │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ complex_recording_1 ┆ false         │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ complex_recording_4 ┆ true          │ │
│ └─────────────────────┴───────────────┘ │
└─────────────────────────────────────────┘\
""")


def test_schema_column_for_selector(complex_dataset_prefix: Path) -> None:
    """Test Schema.column_for_selector with various inputs and error cases."""
    with dl.server.Server() as server:
        client = server.client()
        ds = client.create_dataset("test_dataset")
        ds.register_prefix(complex_dataset_prefix.as_uri())

        schema = ds.schema()

        # Success case: valid selector string returns correct descriptor
        col = schema.column_for_selector("/points:Points2D:colors")
        assert col.entity_path == "/points"
        assert col.component == "Points2D:colors"

        # Success case: ComponentColumnSelector
        selector = dl.catalog.ComponentColumnSelector("/points", "Points2D:positions")
        col = schema.column_for_selector(selector)
        assert col.entity_path == "/points"
        assert col.component == "Points2D:positions"

        # Success case: ComponentColumnDescriptor passthrough (returns equivalent descriptor)
        existing_col = schema.column_for_selector("/text:TextLog:text")
        same_col = schema.column_for_selector(existing_col)
        assert same_col == existing_col

        # LookupError case: column not found
        with pytest.raises(LookupError):
            schema.column_for_selector("/nonexistent:Foo:bar")

        # ValueError case: invalid selector format (no colon)
        with pytest.raises(ValueError):
            schema.column_for_selector("invalid-format-no-colon")
