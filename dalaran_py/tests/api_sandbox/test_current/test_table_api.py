from __future__ import annotations

from typing import TYPE_CHECKING

import dalaran as dl
import datafusion
import pyarrow as pa
from inline_snapshot import snapshot as inline_snapshot

if TYPE_CHECKING:
    import pytest


def test_table_api(tmp_path_factory: pytest.TempPathFactory) -> None:
    with dl.server.Server() as server:
        client = server.client()

        tmp_path = tmp_path_factory.mktemp("my_table")

        table = client.create_table(
            "my_table",
            pa.schema([
                ("dalaran_segment_id", pa.string()),
                ("operator", pa.string()),
            ]),
            tmp_path.as_uri(),
        )

        assert isinstance(table.reader(), datafusion.DataFrame)

        assert str(table.reader().schema()) == inline_snapshot("""\
dalaran_segment_id: string
operator: string
-- schema metadata --
sorbet:version: '0.1.3'\
""")

        df = table.reader()

        assert str(table.reader().collect()) == inline_snapshot("[]")

        table.append(
            dalaran_segment_id=["segment_001", "segment_002"],
            operator=["alice", "bob"],
        )

        assert str(df.sort("dalaran_segment_id")) == inline_snapshot("""\
┌───────────────────────────────────┐
│ METADATA:                         │
│ * version: 0.1.3                  │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ ┌──────────────────┬────────────┐ │
│ │ dalaran_segment_id ┆ operator   │ │
│ │ ---              ┆ ---        │ │
│ │ type: Utf8       ┆ type: Utf8 │ │
│ ╞══════════════════╪════════════╡ │
│ │ segment_001      ┆ alice      │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ segment_002      ┆ bob        │ │
│ └──────────────────┴────────────┘ │
└───────────────────────────────────┘\
""")

        table.append(
            dalaran_segment_id=["segment_003"],
            operator=["carol"],
        )

        assert str(df.sort("dalaran_segment_id")) == inline_snapshot("""\
┌───────────────────────────────────┐
│ METADATA:                         │
│ * version: 0.1.3                  │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ ┌──────────────────┬────────────┐ │
│ │ dalaran_segment_id ┆ operator   │ │
│ │ ---              ┆ ---        │ │
│ │ type: Utf8       ┆ type: Utf8 │ │
│ ╞══════════════════╪════════════╡ │
│ │ segment_001      ┆ alice      │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ segment_002      ┆ bob        │ │
│ ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┤ │
│ │ segment_003      ┆ carol      │ │
│ └──────────────────┴────────────┘ │
└───────────────────────────────────┘\
""")

        assert str(df) == str(client.ctx.table("my_table"))
