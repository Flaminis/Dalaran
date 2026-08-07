#!/usr/bin/env python3
"""
Demonstrates how to use standard input/output with the Dalaran SDK/Viewer.

Usage: `echo 'hello from stdin!' | python main.py | dalaran -`
"""

from __future__ import annotations

import sys

import dalaran as dl  # pip install dalaran-sdk

# sanity-check since all other example scripts take arguments:
assert len(sys.argv) == 1, f"{sys.argv[0]} does not take any arguments"

dl.init("dalaran_example_stdio")
dl.stdout()

input = sys.stdin.buffer.read()

dl.log("stdin", dl.TextDocument(input.decode("utf-8")))
