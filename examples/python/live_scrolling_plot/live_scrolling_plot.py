#!/usr/bin/env python3
"""Show several live plots of random walk data using a scrolling fixed window size."""

from __future__ import annotations

import argparse
import time
from typing import TYPE_CHECKING

import numpy as np

import dalaran as dl  # pip install dalaran-sdk
import dalaran.blueprint as dlb

if TYPE_CHECKING:
    from collections.abc import Iterator


def random_walk_generator() -> Iterator[float]:
    value = 0.0
    while True:
        value += np.random.normal()
        yield value


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot dashboard stress test")
    dl.script_add_args(parser)

    parser.add_argument("--num-plots", type=int, default=6, help="How many different plots?")
    parser.add_argument("--num-series-per-plot", type=int, default=5, help="How many series in each single plot?")
    parser.add_argument("--freq", type=float, default=100, help="Frequency of logging (applies to all series)")
    parser.add_argument("--window-size", type=float, default=5.0, help="Size of the window in seconds")
    parser.add_argument("--duration", type=float, default=60, help="How long to log for in seconds")

    args = parser.parse_args()

    plot_paths = [f"plot_{i}" for i in range(args.num_plots)]
    series_paths = [f"series_{i}" for i in range(args.num_series_per_plot)]

    dl.script_setup(args, "dalaran_example_live_scrolling_plot")

    # Always send the blueprint since it is a function of the data.
    dl.send_blueprint(
        dlb.Grid(
            contents=[
                dlb.TimeSeriesView(
                    origin=plot_path,
                    time_ranges=[
                        dlb.VisibleTimeRange(
                            "time",
                            start=dlb.TimeRangeBoundary.cursor_relative(seconds=-args.window_size),
                            end=dlb.TimeRangeBoundary.cursor_relative(),
                        ),
                    ],
                    plot_legend=dlb.PlotLegend(visible=False),
                )
                for plot_path in plot_paths
            ],
        ),
    )

    # Generate a list of generators for each series in each plot
    values = [[random_walk_generator() for _ in range(args.num_series_per_plot)] for _ in range(args.num_plots)]

    cur_time = time.time()
    end_time = cur_time + args.duration
    time_per_tick = 1.0 / args.freq

    while cur_time < end_time:
        # Advance time and sleep if necessary
        cur_time += time_per_tick
        sleep_for = cur_time - time.time()
        if sleep_for > 0:
            time.sleep(sleep_for)

        if sleep_for < -0.1:
            print(f"Warning: missed logging window by {-sleep_for:.2f} seconds")

        dl.set_time("time", timestamp=cur_time)

        # Output each series based on its generator
        for plot_idx, plot_path in enumerate(plot_paths):
            for series_idx, series_path in enumerate(series_paths):
                dl.log(f"{plot_path}/{series_path}", dl.Scalars(next(values[plot_idx][series_idx])))

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
