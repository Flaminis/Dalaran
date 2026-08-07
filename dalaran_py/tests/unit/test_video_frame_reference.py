from __future__ import annotations

import dalaran as dl
import pytest


def test_video_frame_reference() -> None:
    dl.set_strict_mode(True)

    # Too many args:
    with pytest.raises(ValueError):
        dl.VideoFrameReference(timestamp=dl.components.VideoTimestamp(seconds=12.3), seconds=12.3, nanoseconds=123)
    with pytest.raises(ValueError):
        dl.VideoFrameReference(seconds=12.3, nanoseconds=123)
    with pytest.raises(ValueError):
        dl.VideoFrameReference(timestamp=dl.components.VideoTimestamp(seconds=12.3), nanoseconds=123)
    with pytest.raises(ValueError):
        dl.VideoFrameReference(seconds=12.3, nanoseconds=123)

    # No args:
    with pytest.raises(ValueError):
        dl.VideoFrameReference()

    # Correct usages:
    assert dl.VideoFrameReference(seconds=12.3).timestamp == dl.components.VideoTimestampBatch(
        dl.components.VideoTimestamp(seconds=12.3),
    )
    assert dl.VideoFrameReference(nanoseconds=123).timestamp == dl.components.VideoTimestampBatch(
        dl.components.VideoTimestamp(nanoseconds=123),
    )
    assert dl.VideoFrameReference(
        timestamp=dl.components.VideoTimestamp(nanoseconds=123),
    ).timestamp == dl.components.VideoTimestampBatch(dl.components.VideoTimestamp(nanoseconds=123))
