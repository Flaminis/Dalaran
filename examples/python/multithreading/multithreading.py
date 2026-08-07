#!/usr/bin/env python3
"""Demonstration of using dalaran from multiple threads."""

from __future__ import annotations

import argparse
import random
import threading

import numpy as np
import numpy.typing as npt

import dalaran as dl  # pip install dalaran-sdk


def rect_logger(path: str, color: npt.NDArray[np.float32]) -> None:
    for _ in range(1000):
        rects_xy = np.random.rand(5, 2) * 1024
        rects_wh = np.random.rand(5, 2) * (1024 - rects_xy + 1)
        rects = np.hstack((rects_xy, rects_wh))
        dl.log(path, dl.Boxes2D(array=rects, array_format=dl.Box2DFormat.XYWH, colors=color))


def main() -> None:
    parser = argparse.ArgumentParser(description="Demonstration of using Dalaran from multiple threads.")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_multithreading")

    threads = []
    for i in range(10):
        t = threading.Thread(target=rect_logger, args=(f"thread/{i}", [random.randrange(255) for _ in range(3)]))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
