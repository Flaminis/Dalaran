"""Common fixture used by all tests."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import dalaran as dl
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


DALARAN_DRAFT_PATH = str(Path(__file__).parent)

if DALARAN_DRAFT_PATH not in sys.path:
    sys.path.insert(0, DALARAN_DRAFT_PATH)


def create_simple_dlr(dlr_path: Path, recording_id: str, data_start_value: int) -> None:
    with dl.RecordingStream("dalaran_example_api_test", recording_id=recording_id) as rec:
        rec.save(dlr_path)

        # Avoid `rec.log()` so we dont have the default timelines
        rec.send_columns(
            "/points",
            [dl.TimeColumn("timeline", timestamp=[datetime.datetime(2000, 1, 1, 0, 0, data_start_value)])],
            [
                *dl.Points2D.columns(
                    positions=[[data_start_value, data_start_value + 1], [data_start_value + 3, data_start_value + 4]],
                    colors=[[255, 0, data_start_value % 255], [0, 255, data_start_value % 255]],
                ).partition([2])
            ],
        )


def create_complex_dlr(dlr_path: Path, recording_id: str, data_start_value: int) -> None:
    with dl.RecordingStream("dalaran_example_api_test", recording_id=recording_id) as rec:
        rec.save(dlr_path)

        # Avoid `rec.log()` so we dont have the default timelines
        rec.send_columns(
            "/points",
            [dl.TimeColumn("timeline", timestamp=[datetime.datetime(2000, 1, 1, 0, 0, data_start_value + 1)])],
            [
                *dl.Points2D.columns(
                    positions=[[data_start_value, data_start_value + 1], [data_start_value + 3, data_start_value + 4]],
                    colors=[[255, 0, data_start_value % 255], [0, 255, data_start_value % 255]],
                ).partition([2])
            ],
        )

        rec.send_columns(
            "/text",
            [
                dl.TimeColumn(
                    "timeline",
                    timestamp=[
                        datetime.datetime(2000, 1, 1, 0, 0, data_start_value + 0),
                        datetime.datetime(2000, 1, 1, 0, 0, data_start_value + 2),
                    ],
                )
            ],
            [
                *dl.TextLog.columns(
                    text=["Hello", "World"],
                ).partition([1, 1])
            ],
        )


@pytest.fixture(scope="session")
def simple_recording_path(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Create a temporary recording with little but predicatable content."""

    dlr_path = tmp_path_factory.mktemp("simple_recording") / "simple_recording.dlr"
    create_simple_dlr(dlr_path, "simple_recording_id", 0)
    yield dlr_path


@pytest.fixture(scope="session")
def complex_recording_path(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Create a temporary recording with little but predicatable content."""

    dlr_path = tmp_path_factory.mktemp("complex_recording") / "complex_recording.dlr"
    create_complex_dlr(dlr_path, "complex_recording_id", 0)
    yield dlr_path


@pytest.fixture(scope="session")
def simple_dataset_prefix(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Create a temporary dataset prefix with a few simple recordings."""

    prefix_path = tmp_path_factory.mktemp("simple_dataset_prefix")

    for i in range(3):
        create_simple_dlr(prefix_path / f"simple_recording_{i}.dlr", f"simple_recording_{i}", i)

    yield prefix_path


@pytest.fixture(scope="session")
def complex_dataset_prefix(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Create a temporary dataset prefix with a few complex recordings."""

    prefix_path = tmp_path_factory.mktemp("complex_dataset_prefix")

    for i in range(5):
        create_complex_dlr(prefix_path / f"complex_recording_{i}.dlr", f"complex_recording_{i}", i)

    yield prefix_path
