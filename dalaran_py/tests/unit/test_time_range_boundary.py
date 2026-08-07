from __future__ import annotations

import pytest
import dalaran as dl


def test_time_range_boundary_failure_cases() -> None:
    # Too many arguments for absolute.
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(dl.TimeInt(seq=0), seq=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(dl.TimeInt(seq=0), seconds=123.0)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(dl.TimeInt(seq=0), nanos=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(seq=123, seconds=123.0)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(seq=123, nanos=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(seconds=123, seq=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(seconds=123, nanos=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(nanos=123, seq=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute(nanos=123, seconds=123.0)  # type: ignore[call-overload]

    # No argument for absolute.
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.absolute()  # type: ignore[call-overload]

    # Too many arguments for cursor_relative.
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(dl.TimeInt(seq=0), seq=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(dl.TimeInt(seq=0), seconds=123.0)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(dl.TimeInt(seq=0), nanos=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(seq=123, seconds=123.0)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(seq=123, nanos=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(seconds=123, seq=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(seconds=123, nanos=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(nanos=123, seq=123)  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        dl.TimeRangeBoundary.cursor_relative(nanos=123, seconds=123.0)  # type: ignore[call-overload]


def test_time_range_boundary() -> None:
    # Test infinite.
    assert dl.TimeRangeBoundary.infinite().kind == "infinite"
    assert dl.TimeRangeBoundary.infinite().inner is None

    # Test absolute.
    assert dl.TimeRangeBoundary.absolute(seq=123).kind == "absolute"
    assert dl.TimeRangeBoundary.absolute(seq=123).inner == dl.TimeInt(seq=123)
    assert dl.TimeRangeBoundary.absolute(seq=123).inner == dl.TimeInt(nanos=123)
    assert dl.TimeRangeBoundary.absolute(seconds=1.0).inner == dl.TimeInt(nanos=int(1e9))

    # Test cursor_relative.
    assert dl.TimeRangeBoundary.cursor_relative(seq=123).kind == "cursor_relative"
    assert dl.TimeRangeBoundary.cursor_relative(seq=123).inner == dl.TimeInt(seq=123)
    assert dl.TimeRangeBoundary.cursor_relative(seq=123).inner == dl.TimeInt(nanos=123)
    assert dl.TimeRangeBoundary.cursor_relative(nanos=123).inner == dl.TimeInt(nanos=123)
    assert dl.TimeRangeBoundary.cursor_relative(seconds=1.0).inner == dl.TimeInt(nanos=int(1e9))
    assert dl.TimeRangeBoundary.cursor_relative().kind == "cursor_relative"
    assert dl.TimeRangeBoundary.cursor_relative().inner == dl.TimeInt(seq=0)
