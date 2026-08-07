#!/usr/bin/env python3

from __future__ import annotations

import dalaran as dl  # pip install dalaran-sdk

dl.init("dalaran_example_descriptors_builtin_archetype")
dl.spawn()

dl.log("data", dl.Points3D([[1, 2, 3]], radii=[0.3, 0.2, 0.1]), static=True)

# The tags are indirectly checked by the Rust version (have a look over there
# for more info).
