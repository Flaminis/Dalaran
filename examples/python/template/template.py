#!/usr/bin/env python3
"""Example template."""

from __future__ import annotations

import argparse

import dalaran as dl  # pip install dalaran-sdk


def main() -> None:
    parser = argparse.ArgumentParser(description="Example of using the Dalaran visualizer")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_my_example_name")

    # … example code

    dl.script_teardown(args)


if __name__ == "__main__":
    main()
