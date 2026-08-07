from __future__ import annotations

import os
from argparse import Namespace
from uuid import uuid4

import numpy as np

import dalaran as dl
import dalaran.blueprint as dlb

README = """\
# Blueprint imports

This checks that importing a blueprint into an application always applies it, regardless of its AppID.

You should be seeing a **dataframe view of a plot** on your left, instead of an _actual plot_.
"""


def log_readme() -> None:
    dl.log("readme", dl.TextDocument(README, media_type=dl.MediaType.MARKDOWN), static=True)


def log_external_blueprint() -> None:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".rbl") as tmp:
        dlb.Blueprint(
            dlb.Horizontal(
                dlb.DataframeView(
                    origin="/",
                    query=dlb.archetypes.DataframeQuery(
                        timeline="frame_nr",
                        apply_latest_at=True,
                    ),
                ),
                dlb.TextDocumentView(origin="readme"),
                column_shares=[3, 2],
            ),
        ).save("some_unrelated_blueprint_app_id", tmp.name)

        dl.log_file_from_path(tmp.name)


def log_plots() -> None:
    from math import cos, sin, tau

    def lerp(a, b, t):  # type: ignore[no-untyped-def]
        return a + t * (b - a)

    for t in range(int(tau * 2 * 100.0)):
        dl.set_time("frame_nr", sequence=t)

        sin_of_t = sin(float(t) / 100.0)
        dl.log(
            "trig/sin",
            dl.Scalars(sin_of_t),
            dl.SeriesLines(
                widths=5, colors=lerp(np.array([1.0, 0, 0]), np.array([1.0, 1.0, 0]), (sin_of_t + 1.0) * 0.5)
            ),
        )

        cos_of_t = cos(float(t) / 100.0)
        dl.log(
            "trig/cos",
            dl.Scalars(cos_of_t),
            dl.SeriesLines(
                widths=5,
                colors=lerp(np.array([0.0, 1.0, 1.0]), np.array([0.0, 0.0, 1.0]), (cos_of_t + 1.0) * 0.5),
            ),
        )


def run(args: Namespace) -> None:
    dl.script_setup(
        args,
        f"{os.path.basename(__file__)}",
        recording_id=uuid4(),
    )
    dl.send_blueprint(
        dlb.Blueprint(
            dlb.Horizontal(
                dlb.TimeSeriesView(origin="/"),
                dlb.TextDocumentView(origin="readme"),
                column_shares=[3, 2],
            ),
            dlb.BlueprintPanel(state="collapsed"),
            dlb.SelectionPanel(state="collapsed"),
            dlb.TimePanel(state="collapsed"),
        ),
        make_active=True,
        make_default=True,
    )

    log_readme()
    log_plots()

    log_external_blueprint()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive release checklist")
    dl.script_add_args(parser)
    args = parser.parse_args()
    run(args)
