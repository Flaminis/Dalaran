"""
Helper functions for Dalaran scripts.

These helper functions can be used to wire up common Dalaran features to your script CLi arguments.

Example
-------
```python
import argparse
import dalaran as dl

parser = argparse.ArgumentParser()
dl.script_add_args(parser)
args = parser.parse_args()
dl.script_setup(args, "dalaran_example_application")
# … Run your logging code here …
dl.script_teardown(args)
```

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import dalaran as dl

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from uuid import UUID

    from dalaran.recording_stream import RecordingStream


def script_add_args(parser: ArgumentParser) -> None:
    """
    Add common Dalaran script arguments to `parser`.

    Parameters
    ----------
    parser:
        The parser to add arguments to.

    """
    parser.add_argument("--headless", action="store_true", help="Don't show GUI")
    parser.add_argument(
        "--connect",
        dest="connect",
        action="store_true",
        help="Connect to an external viewer",
    )
    parser.add_argument(
        "--serve",
        dest="serve",
        action="store_true",
        help="Host a GRPC & web server and open a web viewer connecting to it.",
    )
    parser.add_argument("--url", type=str, default=None, help="Connect to this Dalaran URL")
    parser.add_argument("--save", type=str, default=None, help="Save data to a .dlr file at this path")
    parser.add_argument(
        "--stdout",
        dest="stdout",
        action="store_true",
        help="Log data to standard output, to be piped into a Dalaran Viewer",
    )


def script_setup(
    args: Namespace,
    application_id: str,
    *,
    recording_id: str | UUID | None = None,
    default_blueprint: dl.blueprint.BlueprintLike | None = None,
) -> RecordingStream:
    """
    Run common Dalaran script setup actions. Connect to the viewer if necessary.

    Parameters
    ----------
    args:
        The parsed arguments from `parser.parse_args()`.
    application_id:
        The application ID to use for the viewer.
    recording_id:
        Set the recording ID that this process is logging to, as a UUIDv4.

        The default recording_id is based on `multiprocessing.current_process().authkey`
        which means that all processes spawned with `multiprocessing`
        will have the same default recording_id.

        If you are not using `multiprocessing` and still want several different Python
        processes to log to the same Dalaran instance (and be part of the same recording),
        you will need to manually assign them all the same recording_id.
        Any random UUIDv4 will work, or copy the recording id for the parent process.
    default_blueprint:
        Optionally set a default blueprint to use for this application. If the application
        already has an active blueprint, the new blueprint won't become active until the user
        clicks the "reset blueprint" button. If you want to activate the new blueprint
        immediately, instead use the [`dalaran.send_blueprint`][] API.

    """
    dl.init(
        application_id=application_id,
        recording_id=recording_id,
        default_enabled=True,
        strict=True,
    )

    rec: RecordingStream = dl.get_global_data_recording()  # type: ignore[assignment]

    if args.stdout:
        rec.stdout(default_blueprint=default_blueprint)
    elif args.serve:
        connect_to = rec.serve_grpc(default_blueprint=default_blueprint)
        dl.serve_web_viewer(open_browser=True, connect_to=connect_to)
    elif args.connect:
        # Send logging data to separate `dalaran` process.
        # You can omit the argument to connect to the default URL.
        rec.connect_grpc(args.url, default_blueprint=default_blueprint)
    elif args.save is not None:
        rec.save(args.save, default_blueprint=default_blueprint)
    elif not args.headless:
        rec.spawn(default_blueprint=default_blueprint)

    return rec


def script_teardown(args: Namespace) -> None:
    """
    Run common post-actions. Sleep if serving the web viewer.

    Parameters
    ----------
    args:
        The parsed arguments from `parser.parse_args()`.

    """
    if args.serve:
        import time

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Ctrl-C received. Exiting.")
