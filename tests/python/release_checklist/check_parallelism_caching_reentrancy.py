from __future__ import annotations

import math
import os
import random
from argparse import Namespace
from uuid import uuid4

import numpy as np

import dalaran as dl
import dalaran.blueprint as dlb

README = """\
# Parallelism, caching, reentrancy, etc

This check simply puts a lot of pressure on all things parallel.

### Actions

* Scrub the time cursor like crazy: do your worst!

If nothing weird happens, you can close this recording.
"""


def blueprint() -> dlb.BlueprintLike:
    return dlb.Grid(
        dlb.Vertical(*[dlb.TimeSeriesView(name="plots", origin="/plots") for _ in range(3)]),
        dlb.Vertical(*[
            dlb.TimeSeriesView(
                name="plots",
                origin="/plots",
                time_ranges=dlb.VisibleTimeRange(
                    "frame_nr",
                    start=dlb.TimeRangeBoundary.cursor_relative(seq=50 - i * 10),
                    end=dlb.TimeRangeBoundary.cursor_relative(seq=50 - i * 10 + 10),
                ),
            )
            for i in range(10)
        ]),
        dlb.Vertical(*[dlb.TextLogView(name="logs", origin="/text") for _ in range(3)]),
        dlb.Vertical(*[dlb.Spatial2DView(name="2D", origin="/2D") for _ in range(3)]),
        dlb.Vertical(*[
            dlb.Spatial2DView(
                name="2D",
                origin="/2D",
                time_ranges=dlb.VisibleTimeRange(
                    "frame_nr",
                    start=dlb.TimeRangeBoundary.infinite(),
                    end=dlb.TimeRangeBoundary.cursor_relative(),
                ),
            )
            for _ in range(3)
        ]),
        dlb.Vertical(*[dlb.Spatial3DView(name="3D", origin="/3D") for _ in range(3)]),
        dlb.Vertical(*[
            dlb.Spatial3DView(
                name="3D",
                origin="/3D",
                time_ranges=dlb.VisibleTimeRange(
                    "frame_nr",
                    start=dlb.TimeRangeBoundary.infinite(),
                    end=dlb.TimeRangeBoundary.infinite(),
                ),
            )
            for _ in range(3)
        ]),
        dlb.TextDocumentView(origin="readme"),
        grid_columns=4,
    )


def log_readme() -> None:
    dl.log("readme", dl.TextDocument(README, media_type=dl.MediaType.MARKDOWN), static=True)


def log_text_logs() -> None:
    for t in range(100):
        dl.set_time("frame_nr", sequence=t)
        dl.log("text", dl.TextLog("Something good happened", level=dl.TextLogLevel.INFO))
        dl.log("text", dl.TextLog("Something bad happened", level=dl.TextLogLevel.ERROR))


def log_plots() -> None:
    from math import cos, sin, tau

    dl.log("plots/sin", dl.SeriesLines(colors=[255, 0, 0], names="sin(0.01t)"), static=True)
    dl.log("plots/cos", dl.SeriesLines(colors=[0, 255, 0], names="cos(0.01t)"), static=True)

    for t in range(int(tau * 2 * 10.0)):
        dl.set_time("frame_nr", sequence=t)

        sin_of_t = sin(float(t) / 10.0)
        dl.log("plots/sin", dl.Scalars(sin_of_t))

        cos_of_t = cos(float(t) / 10.0)
        dl.log("plots/cos", dl.Scalars(cos_of_t))


def log_spatial() -> None:
    for t in range(100):
        dl.set_time("frame_nr", sequence=t)

        positions3d = [
            [math.sin((i + t) * 0.2) * 5, math.cos((i + t) * 0.2) * 5 - 10.0, i * 0.4 - 5.0] for i in range(100)
        ]

        dl.log(
            "3D/points",
            dl.Points3D(
                np.array(positions3d),
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )
        dl.log(
            "3D/lines",
            dl.LineStrips3D(
                np.array(positions3d),
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )
        dl.log(
            "3D/arrows",
            dl.Arrows3D(
                vectors=np.array(positions3d),
                radii=0.1,
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )
        dl.log(
            "3D/boxes",
            dl.Boxes3D(
                half_sizes=np.array(positions3d),
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )

        positions2d = [[math.sin(i * math.tau / 100.0) * t, math.cos(i * math.tau / 100.0) * t] for i in range(100)]

        dl.log(
            "2D/points",
            dl.Points2D(
                np.array(positions2d),
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )
        dl.log(
            "2D/lines",
            dl.LineStrips2D(
                np.array(positions2d),
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )
        dl.log(
            "2D/arrows",
            dl.Arrows2D(
                vectors=np.array(positions2d),
                radii=0.1,
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )
        dl.log(
            "2D/boxes",
            dl.Boxes2D(
                half_sizes=np.array(positions2d),
                labels=[str(i) for i in range(t, t + 100)],
                colors=np.array([[random.randrange(255) for _ in range(3)] for _ in range(t, t + 100)]),
            ),
        )


def run(args: Namespace) -> None:
    dl.script_setup(args, f"{os.path.basename(__file__)}", recording_id=uuid4())
    dl.send_blueprint(blueprint(), make_active=True, make_default=True)

    log_readme()
    log_text_logs()
    log_plots()
    log_spatial()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive release checklist")
    dl.script_add_args(parser)
    args = parser.parse_args()
    run(args)
