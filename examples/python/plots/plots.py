#!/usr/bin/env python3
"""
Demonstrates how to log simple plots with the Dalaran SDK.

Run:
```sh
./examples/python/plot/plots.py
```
"""

from __future__ import annotations

import argparse
import random
from math import cos, sin, tau

import numpy as np

import dalaran as dl
import dalaran.blueprint as dlb

DESCRIPTION = """
# Plots
This example shows various plot types that you can create using Dalaran. Common usecases for such plots would be logging
losses or metrics over time, histograms, or general function plots.

The full source code for this example is available [on GitHub](https://github.com/Flaminis/Dalaran/blob/latest/examples/python/plots).
""".strip()


def log_bar_chart() -> None:
    dl.set_time("frame_nr", sequence=0)
    # Log a gauss bell as a bar chart
    mean = 0
    std = 1
    variance = np.square(std)
    x = np.arange(-5, 5, 0.1)
    y = np.exp(-np.square(x - mean) / 2 * variance) / (np.sqrt(2 * np.pi * variance))
    dl.log("bar_chart", dl.BarChart(y))


def log_parabola() -> None:
    # Time-independent styling can be achieved by logging static components to the data store. Here, by using the
    # `SeriesLines` archetype, we further hint the viewer to use the line plot visualizer.
    # Alternatively, you can achieve time-independent styling using overrides, as is everywhere else in this example
    # (see the `main()` function).
    dl.log("curves/parabola", dl.SeriesLines(names="f(t) = (0.01t - 3)³ + 1"), static=True)

    # Log a parabola as a time series
    for t in range(0, 1000, 10):
        dl.set_time("frame_nr", sequence=t)

        f_of_t = (t * 0.01 - 5) ** 3 + 1
        width = np.clip(abs(f_of_t) * 0.1, 0.5, 10.0)
        color = [255, 255, 0]
        if f_of_t < -10.0:
            color = [255, 0, 0]
        elif f_of_t > 10.0:
            color = [0, 255, 0]

        # Note: by using the `dl.SeriesLines` archetype, we hint the viewer to use the line plot visualizer.
        dl.log(
            "curves/parabola",
            dl.Scalars(f_of_t),
            dl.SeriesLines(widths=width, colors=color),
        )


def log_trig() -> None:
    for t in range(int(tau * 2 * 100.0)):
        dl.set_time("frame_nr", sequence=t)

        sin_of_t = sin(float(t) / 100.0)
        dl.log("trig/sin", dl.Scalars(sin_of_t))

        cos_of_t = cos(float(t) / 100.0)
        dl.log("trig/cos", dl.Scalars(cos_of_t))


def log_spiral() -> None:
    times = np.arange(int(tau * 2 * 100.0))
    theta = times / 100.0

    x = theta * np.cos(theta)
    y = theta * np.sin(theta)

    # want this in column major, and numpy is row-major by default
    scalars = np.array((x, y)).T
    dl.send_columns(
        "spiral",
        indexes=[dl.TimeColumn("frame_nr", sequence=times)],
        columns=[*dl.Scalars.columns(scalars=scalars)],
    )


def log_classification() -> None:
    for t in range(0, 1000, 2):
        dl.set_time("frame_nr", sequence=t)

        f_of_t = (2 * 0.01 * t) + 2
        dl.log("classification/line", dl.Scalars(f_of_t))

        g_of_t = f_of_t + random.uniform(-5.0, 5.0)
        if g_of_t < f_of_t - 1.5:
            color = [255, 0, 0]
        elif g_of_t > f_of_t + 1.5:
            color = [0, 255, 0]
        else:
            color = [255, 255, 255]
        marker_size = abs(g_of_t - f_of_t)

        # Note: this log call doesn't include any hint as to which visualizer to use. We use a blueprint visualizer
        # override instead (see `main()`)
        dl.log(
            "classification/samples",
            dl.Scalars(g_of_t),
            dl.SeriesPoints(colors=color, marker_sizes=marker_size),
        )


def log_states() -> None:
    # Configure how each raw state value is displayed (label, color). This is
    # time-independent, so we log it as static.
    dl.log(
        "states/trend",
        dl.StateConfiguration(
            values=["rising", "falling"],
            labels=["Rising", "Falling"],
            colors=[0x4CAF50FF, 0xEF5350FF],
        ),
        static=True,
    )
    dl.log(
        "states/level",
        dl.StateConfiguration(
            values=["low", "mid", "high"],
            # Wrapped as `np.uint32` so that a length-3 list isn't mistaken for a single RGB color.
            colors=np.array([0x5C6BC0FF, 0x9E9E9EFF, 0xFFB300FF], dtype=np.uint32),
        ),
        static=True,
    )

    # Derive discrete states from the same sine wave as `log_trig`, and log a
    # `StateChange` whenever a state transition happens. The state timeline view
    # displays these as horizontal colored lanes over time.
    trend = None
    level = None
    for t in range(int(tau * 2 * 100.0)):
        dl.set_time("frame_nr", sequence=t)

        sin_of_t = sin(float(t) / 100.0)
        cos_of_t = cos(float(t) / 100.0)

        new_trend = "rising" if cos_of_t >= 0.0 else "falling"
        if new_trend != trend:
            trend = new_trend
            dl.log("states/trend", dl.StateChange(state=trend))

        new_level = "high" if sin_of_t > 0.5 else "low" if sin_of_t < -0.5 else "mid"
        if new_level != level:
            level = new_level
            dl.log("states/level", dl.StateChange(state=level))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="demonstrates how to integrate python's native `logging` with the Dalaran SDK",
    )
    dl.script_add_args(parser)
    args = parser.parse_args()

    blueprint = dlb.Blueprint(
        dlb.Horizontal(
            dlb.Vertical(
                dlb.Grid(
                    dlb.BarChartView(name="Bar Chart", origin="/bar_chart"),
                    dlb.TimeSeriesView(
                        name="Curves",
                        origin="/curves",
                    ),
                    dlb.TimeSeriesView(
                        name="Trig",
                        origin="/trig",
                        overrides={
                            "/trig/sin": dl.SeriesLines.from_fields(colors=[255, 0, 0], names="sin(0.01t)"),
                            "/trig/cos": dl.SeriesLines.from_fields(colors=[0, 255, 0], names="cos(0.01t)"),
                        },
                    ),
                    dlb.TimeSeriesView(
                        name="Classification",
                        origin="/classification",
                        overrides={
                            "classification/line": dl.SeriesLines.from_fields(colors=[255, 255, 0], widths=3.0),
                            # This ensures that the `SeriesPoints` visualizers is used for this entity.
                            "classification/samples": dl.SeriesPoints(),
                        },
                    ),
                ),
                dlb.Horizontal(
                    dlb.TimeSeriesView(
                        name="Spiral",
                        origin="/spiral",
                        overrides={
                            "spiral": dl.SeriesLines.from_fields(names=["0.01t cos(0.01t)", "0.01t sin(0.01t)"])
                        },  # type: ignore[arg-type]
                    ),
                    dlb.StateTimelineView(name="States", origin="/states"),
                ),
                row_shares=[2, 1],
            ),
            dlb.TextDocumentView(name="Description", origin="/description"),
            column_shares=[3, 1],
        ),
        dlb.SelectionPanel(state="collapsed"),
        dlb.TimePanel(state="collapsed"),
    )

    dl.script_setup(args, "dalaran_example_plot", default_blueprint=blueprint)

    dl.log("description", dl.TextDocument(DESCRIPTION, media_type=dl.MediaType.MARKDOWN), static=True)
    log_bar_chart()
    log_parabola()
    log_trig()
    log_spiral()
    log_classification()
    log_states()

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
