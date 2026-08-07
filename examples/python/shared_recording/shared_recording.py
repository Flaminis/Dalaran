#!/usr/bin/env python3
"""Demonstrates how to use `RecordingId`s to build a single recording from multiple processes."""

from __future__ import annotations

import os
import sys

import dalaran as dl  # pip install dalaran-sdk


def main() -> None:
    # sanity-check since all other example scripts take arguments:
    assert len(sys.argv) == 1, f"{sys.argv[0]} does not take any arguments"

    dl.init("dalaran_example_shared_recording", recording_id="my_shared_recording", spawn=True)

    dl.log("updates", dl.TextLog(f"hello from {os.getpid()}"))

    print("Run me again to append more data to the recording!")


if __name__ == "__main__":
    main()
