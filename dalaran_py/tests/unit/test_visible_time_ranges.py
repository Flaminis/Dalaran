from __future__ import annotations

import dalaran as dl
import pytest


def test_visible_time_ranges_warns_on_duplicate_entry() -> None:
    dl.set_strict_mode(True)

    with pytest.raises(ValueError):
        dl.blueprint.archetypes.VisibleTimeRanges([
            dl.VisibleTimeRange("timeline", start=dl.TimeRangeBoundary.infinite(), end=dl.TimeRangeBoundary.infinite()),
            dl.VisibleTimeRange(
                "timeline",
                start=dl.TimeRangeBoundary.absolute(seconds=1.0),
                end=dl.TimeRangeBoundary.cursor_relative(),
            ),
        ])


def test_visible_time_ranges_from_single() -> None:
    time_range = dl.VisibleTimeRange(
        "timeline",
        start=dl.TimeRangeBoundary.cursor_relative(),
        end=dl.TimeRangeBoundary.absolute(seconds=1.0),
    )
    assert dl.blueprint.archetypes.VisibleTimeRanges(time_range) == dl.blueprint.archetypes.VisibleTimeRanges([
        time_range,
    ])

    assert dl.blueprint.archetypes.VisibleTimeRanges(time_range) == dl.blueprint.archetypes.VisibleTimeRanges(
        timeline="timeline",
        start=dl.TimeRangeBoundary.cursor_relative(),
        end=dl.TimeRangeBoundary.absolute(seconds=1.0),
    )

    assert dl.blueprint.archetypes.VisibleTimeRanges(time_range) == dl.blueprint.archetypes.VisibleTimeRanges(
        timeline="timeline",
        range=dl.TimeRange(dl.TimeRangeBoundary.cursor_relative(), dl.TimeRangeBoundary.absolute(seconds=1.0)),
    )


def test_visible_time_ranges_invalid_parameters() -> None:
    time_range = dl.VisibleTimeRange(
        "timeline",
        start=dl.TimeRangeBoundary.cursor_relative(),
        end=dl.TimeRangeBoundary.absolute(seconds=1.0),
    )

    with pytest.raises(ValueError):
        # Numpy correctly flags this as an invalid overload, make sure it also throws.
        dl.blueprint.archetypes.VisibleTimeRanges(
            ranges=[time_range],
            timeline="timeline",
            start=dl.TimeRangeBoundary.cursor_relative(),
            end=dl.TimeRangeBoundary.absolute(seconds=1.0),
        )  # type: ignore[call-overload]

    with pytest.raises(ValueError):
        # Numpy correctly flags this as an invalid overload, make sure it also throws.
        dl.blueprint.archetypes.VisibleTimeRanges(
            timeline="timeline",
            start=dl.TimeRangeBoundary.cursor_relative(),
            end=dl.TimeRangeBoundary.absolute(seconds=1.0),
            range=dl.TimeRange(dl.TimeRangeBoundary.cursor_relative(), dl.TimeRangeBoundary.absolute(seconds=1.0)),
        )  # type: ignore[call-overload]
