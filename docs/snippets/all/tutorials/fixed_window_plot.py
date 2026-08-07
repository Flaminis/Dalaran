#!/usr/bin/env python3
"""A live plot of a random walk using a scrolling fixed window size."""

from __future__ import annotations

import time

import numpy as np

import dalaran as dl  # pip install dalaran-sdk
import dalaran.blueprint as dlb

dl.init("dalaran_example_fixed_window_plot", spawn=True)

dl.send_blueprint(
    dlb.TimeSeriesView(
        origin="random_walk",
        time_ranges=dlb.VisibleTimeRange(
            "time",
            start=dlb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
            end=dlb.TimeRangeBoundary.cursor_relative(),
        ),
    ),
)

cur_time = time.time()
value = 0.0

while True:
    cur_time += 0.01
    sleep_for = cur_time - time.time()
    if sleep_for > 0:
        time.sleep(sleep_for)

    value += np.random.normal()

    dl.set_time("time", timestamp=cur_time)

    dl.log("random_walk", dl.Scalars(value))
