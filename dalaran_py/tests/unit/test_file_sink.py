"""Tests for the `FileSink` / `save` / `stdout` `write_footer` opt-out."""

from __future__ import annotations

from typing import TYPE_CHECKING

import dalaran as dl

if TYPE_CHECKING:
    import pathlib

APP_ID = "dalaran_example_test_file_sink"

# The trailing DLR `StreamFooter` frame always ends with the bytes `RRF2` followed by
# `FOOT`, located at `file_len - 12 .. file_len - 4`.
# See `dl_log_encoding::dlr::frames::StreamFooter` for the definition.
_STREAM_FOOTER_FOURCC = b"RRF2"
_STREAM_FOOTER_IDENTIFIER = b"FOOT"


def _has_stream_footer(path: pathlib.Path) -> bool:
    """Return True if the file at `path` ends with a valid DLR `StreamFooter` trailer."""
    data = path.read_bytes()
    if len(data) < 12:
        return False
    return data[-12:-8] == _STREAM_FOOTER_FOURCC and data[-8:-4] == _STREAM_FOOTER_IDENTIFIER


def _log_some(rec: dl.RecordingStream) -> None:
    for i in range(10):
        rec.log("signal", dl.Scalars(float(i)))


def test_save_default_writes_footer(tmp_path: pathlib.Path) -> None:
    """`RecordingStream.save(path)` defaults to writing a footer."""
    dlr = tmp_path / "default.dlr"
    rec = dl.RecordingStream(APP_ID)
    rec.save(dlr)
    _log_some(rec)
    rec.disconnect()

    assert _has_stream_footer(dlr), "default save() must produce a footer-bearing file"


def test_save_write_footer_false_omits_footer(tmp_path: pathlib.Path) -> None:
    """`RecordingStream.save(path, write_footer=False)` produces a footer-less file."""
    dlr = tmp_path / "no_footer.dlr"
    rec = dl.RecordingStream(APP_ID)
    rec.save(dlr, write_footer=False)
    _log_some(rec)
    rec.disconnect()

    assert not _has_stream_footer(dlr), "save(…, write_footer=False) must produce a footer-less file"


def test_module_save_write_footer_false(tmp_path: pathlib.Path) -> None:
    """The module-level `dl.save(…, write_footer=False)` honours the flag."""
    dlr = tmp_path / "module_no_footer.dlr"
    dl.init(APP_ID + "_module")
    dl.save(dlr, write_footer=False)
    for i in range(10):
        dl.log("signal", dl.Scalars(float(i)))
    dl.disconnect()

    assert not _has_stream_footer(dlr)


def test_filesink_class_default_writes_footer(tmp_path: pathlib.Path) -> None:
    """The `dl.FileSink(path)` class defaults to writing a footer (legacy call shape)."""
    dlr = tmp_path / "filesink_default.dlr"
    rec = dl.RecordingStream(APP_ID)
    rec.set_sinks(dl.FileSink(dlr))
    _log_some(rec)
    rec.disconnect()

    assert _has_stream_footer(dlr)


def test_filesink_class_write_footer_false(tmp_path: pathlib.Path) -> None:
    """The `dl.FileSink(path, write_footer=False)` class honours the kw-only flag."""
    dlr = tmp_path / "filesink_no_footer.dlr"
    rec = dl.RecordingStream(APP_ID)
    rec.set_sinks(dl.FileSink(dlr, write_footer=False))
    _log_some(rec)
    rec.disconnect()

    assert not _has_stream_footer(dlr)
