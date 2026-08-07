from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow as pa
import pytest
import dalaran_draft as dl
from inline_snapshot import snapshot as inline_snapshot

from .utils import sorted_schema_str

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def dlr_paths(complex_dataset_prefix: Path) -> Generator[list[Path], None, None]:
    """Paths to some dlr files."""

    yield sorted(complex_dataset_prefix.glob("*.dlr"), key=lambda p: p.stem)


def test_dataset_basics(complex_dataset_prefix: Path) -> None:
    with dl.server.Server() as server:
        client = server.client()

        ds = client.create_dataset("basic_dataset")

        ds.register_prefix(complex_dataset_prefix.as_uri()).wait()

        segment_df = ds.segment_table()

        assert segment_df.schema().to_string(show_field_metadata=False) == inline_snapshot("""\
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

        df_schema = segment_df.schema()
        for batch in segment_df.collect():
            assert batch.schema.equals(df_schema, check_metadata=True)
        assert str(
            segment_df.drop(
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


def test_dataset_register(dlr_paths: list[Path]) -> None:
    with dl.server.Server() as server:
        client = server.client()

        ds = client.create_dataset("dataset")

        # Single DLR, default layer name
        ds.register([dlr_paths[0].as_uri()]).wait()

        # Single DLR, override layer name
        ds.register([dlr_paths[1].as_uri()], layer_name="extra").wait()

        # Multiple RRDs, multiple layer names
        ds.register([p.as_uri() for p in dlr_paths[2:4]], layer_name=["fiz", "fuz"]).wait()

        # Multiple RRDs, single layer name
        ds.register([p.as_uri() for p in dlr_paths], layer_name="more").wait()

        with pytest.raises(ValueError):
            ds.register([p.as_uri() for p in dlr_paths], layer_name=["not", "enough"]).wait()

        df = ds._manifest().select("dalaran_layer_name", "dalaran_segment_id").sort("dalaran_layer_name", "dalaran_segment_id")
        df_schema = df.schema()
        for batch in df.collect():
            assert batch.schema.equals(df_schema, check_metadata=True)

        assert str(df) == inline_snapshot(
            """\
┌───────────────────────────────────────────────┐
│ METADATA:                                     │
│ * version: 0.1.3                              │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ ┌─────────────────────┬─────────────────────┐ │
│ │ dalaran_layer_name    ┆ dalaran_segment_id    │ │
│ │ ---                 ┆ ---                 │ │
│ │ type: non-null Utf8 ┆ type: non-null Utf8 │ │
│ ╞═════════════════════╪═════════════════════╡ │
│ │ base                ┆ complex_recording_0 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ extra               ┆ complex_recording_1 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ fiz                 ┆ complex_recording_2 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ fuz                 ┆ complex_recording_3 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ more                ┆ complex_recording_0 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ more                ┆ complex_recording_1 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ more                ┆ complex_recording_2 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ more                ┆ complex_recording_3 │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ more                ┆ complex_recording_4 │ │
│ └─────────────────────┴─────────────────────┘ │
└───────────────────────────────────────────────┘\
"""
        )


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

        assert sorted_schema_str(ds.arrow_schema(), with_metadata=True) == inline_snapshot("""\
/points:Points2D:colors: list<item: uint32>
  -- field metadata --
  dalaran:archetype: 'dalaran.archetypes.Points2D'
  dalaran:component: 'Points2D:colors'
  dalaran:component_type: 'dalaran.components.Color'
  dalaran:entity_path: '/points'
  dalaran:kind: 'data'
/points:Points2D:positions: list<item: fixed_size_list<item: float not null>[2]>
  -- field metadata --
  dalaran:archetype: 'dalaran.archetypes.Points2D'
  dalaran:component: 'Points2D:positions'
  dalaran:component_type: 'dalaran.components.Position2D'
  dalaran:entity_path: '/points'
  dalaran:kind: 'data'
/text:TextLog:text: list<item: string>
  -- field metadata --
  dalaran:archetype: 'dalaran.archetypes.TextLog'
  dalaran:component: 'TextLog:text'
  dalaran:component_type: 'dalaran.components.Text'
  dalaran:entity_path: '/text'
  dalaran:kind: 'data'
property:RecordingInfo:start_time: list<item: int64>
  -- field metadata --
  dalaran:archetype: 'dalaran.archetypes.RecordingInfo'
  dalaran:component: 'RecordingInfo:start_time'
  dalaran:component_type: 'dalaran.components.Timestamp'
  dalaran:entity_path: '/__properties'
  dalaran:is_static: 'true'
  dalaran:kind: 'data'
dalaran.controls.RowId: fixed_size_binary[16]
  -- field metadata --
  ARROW:extension:metadata: '{"namespace":"row"}'
  ARROW:extension:name: 'dalaran.datatypes.TUID'
  dalaran:kind: 'control'
timeline: timestamp[ns]
  -- field metadata --
  dalaran:index_name: 'timeline'
  dalaran:kind: 'index'
-- schema metadata --
sorbet:version: '0.1.3'\
""")


def test_dataset_metadata(complex_dataset_prefix: Path) -> None:
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
        )

        meta.append(
            dalaran_segment_id=["complex_recording_0", "complex_recording_1", "complex_recording_4"],
            success=[True, False, True],
        )

        df = meta.reader()
        df_schema = df.schema()
        for batch in df.collect():
            assert batch.schema.equals(df_schema, check_metadata=True)

        assert (str(df)) == inline_snapshot("""\
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


def test_manifest_diagnostic_data(complex_dataset_prefix: Path) -> None:
    """Test the include_diagnostic_data parameter on _manifest()."""
    with dl.server.Server() as server:
        client = server.client()
        ds = client.create_dataset("dataset")
        ds.register_prefix(complex_dataset_prefix.as_uri()).wait()

        # Default: dalaran_registration_status column should not be present
        manifest = ds._manifest()
        column_names = [f.name for f in manifest.schema()]
        assert "dalaran_registration_status" not in column_names

        # With include_diagnostic_data=True: column should be present
        manifest_diag = ds._manifest(include_diagnostic_data=True)
        column_names_diag = [f.name for f in manifest_diag.schema()]
        assert "dalaran_registration_status" in column_names_diag

        # In dl_server, all registrations are successful (Done=1)
        # since schema conflicts fail synchronously
        statuses = manifest_diag.select("dalaran_registration_status").to_arrow_table().to_pydict()
        assert all(s == "done" for s in statuses["dalaran_registration_status"])
