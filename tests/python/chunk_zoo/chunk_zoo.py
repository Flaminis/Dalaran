"""
A collection of delightfully unique chunk specimens, for science.

IMPORTANT: the viewer should be set with `DALARAN_CHUNK_MAX_BYTES=0` to disable the compactor.

To add new specimens to the zoo, add a function whose name starts with "specimen_".
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import numpy as np

import dalaran as dl

if TYPE_CHECKING:
    from collections.abc import Sequence


def frame_times(t: int | Sequence[int], *args: int) -> list[dl.TimeColumn]:
    if isinstance(t, int):
        t = [t]
    else:
        t = list(t)
    if args:
        t.extend(args)
    return [dl.TimeColumn("frame", sequence=t)]


def set_frame_time(t: int) -> None:
    dl.set_time("frame", sequence=t)


def specimen_two_rows_span_two_chunks() -> None:
    """Two rows spanning two chunks."""

    dl.send_columns("/rows_span_two_chunks", frame_times(0, 2), dl.Points2D.columns(positions=[(0, 1), (2, 3)]))
    dl.send_columns("/rows_span_two_chunks", frame_times(0, 2), dl.Points2D.columns(radii=[10, 11]))


def specimen_two_rows_span_two_chunks_sparse() -> None:
    """Two rows spanning two chunks with partially matching timestamps (so sparse results)."""

    dl.send_columns(
        "/rows_span_two_chunks_sparse",
        frame_times(0, 2, 3),
        dl.Points2D.columns(positions=[(0, 1), (2, 3), (4, 5)]),
    )
    dl.send_columns("/rows_span_two_chunks_sparse", frame_times(0, 2, 4), dl.Points2D.columns(radii=[10, 11, 12]))


def specimen_archetype_with_clamp_join_semantics() -> None:
    """Single row of an archetype with clamp join semantics (Points2D)."""
    dl.send_columns(
        "/archetype_with_clamp_join_semantics",
        frame_times(0),
        [
            *dl.Points2D.columns(
                positions=[(i, i) for i in range(10)],
            ).partition([10]),
            *dl.Points2D.columns(radii=2),
        ],
    )


def specimen_archetype_with_latest_at_semantics() -> None:
    """Archetype spread over a multi-row chunk and a single row chunk, with latest-at semantics."""
    dl.send_columns(
        "/archetype_chunk_with_latest_at_semantics",
        frame_times(range(10)),
        dl.Points2D.columns(positions=[(i, i) for i in range(10)], class_ids=range(10)),
    )

    set_frame_time(5)
    dl.log("/archetype_chunk_with_latest_at_semantics", dl.Points2D.from_fields(radii=2))


def specimen_archetype_with_clamp_join_semantics_two_chunks() -> None:
    """Single row of an archetype with clamp join semantics (Points2D), across two chunks."""
    dl.send_columns(
        "/archetype_with_clamp_join_semantics_two_batches",
        frame_times(0),
        dl.Points2D.columns(positions=[(i, i) for i in range(10)]).partition([10]),
    )

    dl.send_columns(
        "/archetype_with_clamp_join_semantics_two_batches",
        frame_times(0),
        dl.Points2D.columns(radii=2),
    )


def specimen_archetype_without_clamp_join_semantics() -> None:
    """Single row of an archetype without clamp join semantics (Mesh3D)."""
    dl.send_columns(
        "/archetype_without_clamp_join_semantics",
        frame_times(0),
        [
            *dl.Mesh3D.columns(
                vertex_positions=[(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
                vertex_colors=[(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)],
            ).partition([4]),
            *dl.Mesh3D.columns(triangle_indices=[(0, 1, 2), (0, 2, 3)]).partition([2]),
        ],
    )


def specimen_many_rows_with_mismatched_instance_count() -> None:
    """Points2D across many timestamps with varying and mismatch instance counts."""

    # Useful for dataframe view row expansion testing.

    np.random.seed(0)
    positions_partitions = np.random.randint(
        3,
        15,
        size=100,
    )
    batch_size = int(np.sum(positions_partitions))

    # Shuffle the color partitions to induce the mismatch
    colors_partitions = positions_partitions.copy()
    np.random.shuffle(colors_partitions)

    positions = np.random.rand(batch_size, 2)
    colors = np.random.randint(0, 255, size=(batch_size, 4))

    dl.send_columns(
        "/many_rows_with_mismatched_instance_count",
        frame_times(range(len(positions_partitions))),
        [
            *dl.Points2D.columns(positions=positions).partition(positions_partitions),
            *dl.Points2D.columns(colors=colors).partition(colors_partitions),
        ],
    )


# TODO(ab): add variants (unordered, overlapping timestamps, etc.)
def specimen_scalars_interlaced_in_two_chunks() -> None:
    """Scalar column stored in two chunks, with interlaced timestamps."""
    dl.send_columns(
        "/scalars_interlaced_in_two_chunks",
        frame_times(0, 2, 5, 6, 8),
        dl.Scalars.columns(scalars=[0, 2, 5, 6, 8]),
    )
    dl.send_columns(
        "/scalars_interlaced_in_two_chunks",
        frame_times(1, 3, 7),
        dl.Scalars.columns(scalars=[1, 3, 7]),
    )


def specimen_archetype_chunk_with_clear() -> None:
    """Archetype spread on multi-row and single-row chunks, with a `Clear` in the middle."""
    dl.send_columns(
        "/archetype_chunk_with_clear",
        frame_times(range(10)),
        dl.Points2D.columns(positions=[(i, i) for i in range(10)], class_ids=range(10)),
    )

    set_frame_time(0)
    dl.log("/archetype_chunk_with_clear", dl.Points2D.from_fields(radii=2))

    set_frame_time(5)
    dl.log("/archetype_chunk_with_clear", dl.Clear(recursive=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Logs a bunch of chunks of various typologies. Use `DALARAN_CHUNK_MAX_BYTES=0`!",
    )
    parser.add_argument("--filter", type=str, help="Only run specimens whose name contains this substring")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_chunk_zoo", default_blueprint=dl.blueprint.TextDocumentView(origin="/info"))

    # Round up the specimens
    specimens = [
        globals()[name]
        for name in globals()
        if name.startswith("specimen_") and callable(globals()[name]) and (not args.filter or args.filter in name)
    ]

    specimen_list = "\n".join([f"| {s.__name__.removeprefix('specimen_')} | {s.__doc__} |" for s in specimens])
    markdown = (
        "# Chunk Zoo\n\n"
        "This recording contains a variety of chunks of various typologies, for testing purposes.\n\n"
        "**IMPORTANT**: The viewer should be set with `DALARAN_CHUNK_MAX_BYTES=0` to disable the compactor.\n\n"
        "### Specimens\n\n"
        f"| **Item** | **Description** |\n| --- | --- |\n{specimen_list}"
    )
    dl.log("info", dl.TextDocument(text=markdown, media_type="text/markdown"), static=True)

    # Set the specimens loose
    for specimen in specimens:
        specimen()


if __name__ == "__main__":
    main()
