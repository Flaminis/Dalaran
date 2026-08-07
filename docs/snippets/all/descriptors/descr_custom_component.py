#!/usr/bin/env python3

from __future__ import annotations

import dalaran as dl  # pip install dalaran-sdk

dl.init("dalaran_example_descriptors_custom_component")
dl.spawn()

positions = dl.components.Position3DBatch([1, 2, 3]).described(
    dl.ComponentDescriptor(
        "user.CustomArchetype:custom_positions",
        archetype="user.CustomArchetype",
        component_type="user.CustomPosition3D",
    ),
)
dl.log("data", [positions], static=True)

# The tags are indirectly checked by the Rust version (have a look over there
# for more info).
