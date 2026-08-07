from __future__ import annotations

import tempfile

import dalaran as dl

import dalaran_bindings  # noqa: TID251


def test_disconnect_on_cleanup() -> None:
    with tempfile.TemporaryDirectory() as dirpath:
        rec_path = f"{dirpath}/rec.dlr"

        def create_recording() -> None:
            rec = dl.RecordingStream("dalaran_example_construct")
            rec.save(rec_path)
            rec.log("x", dl.Points2D(positions=[(1, 2), (3, 4)]))

        create_recording()

        assert dalaran_bindings.check_for_dlr_footer(rec_path)


def test_disconnect_on_cleanup_with_ctx() -> None:
    with tempfile.TemporaryDirectory() as dirpath:
        rec_path = f"{dirpath}/rec.dlr"

        def create_recording() -> None:
            with dl.RecordingStream("dalaran_example_ctx") as rec:
                rec.save(rec_path)
                rec.log("x", dl.Points2D(positions=[(1, 2), (3, 4)]))

        create_recording()

        assert dalaran_bindings.check_for_dlr_footer(rec_path)


def test_footer_written_at_context_exit() -> None:
    """The footer must be present as soon as the `with`-block exits — before `rec` is GC'd."""
    with tempfile.TemporaryDirectory() as dirpath:
        rec_path = f"{dirpath}/rec.dlr"

        rec = dl.RecordingStream("dalaran_example_finalize_at_exit")
        with rec:
            rec.save(rec_path)
            rec.log("x", dl.Points2D(positions=[(1, 2), (3, 4)]))

        # `rec` is still alive here — no GC has happened. The footer must already be on disk.
        assert dalaran_bindings.check_for_dlr_footer(rec_path)

        # Keep `rec` alive past the assertion so `__del__` can't sneak in and rescue a missing footer.
        del rec


if __name__ == "__main__":
    test_disconnect_on_cleanup()
