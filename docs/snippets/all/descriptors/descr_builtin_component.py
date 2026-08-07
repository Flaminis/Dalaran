#!/usr/bin/env python3

from __future__ import annotations

import dalaran as dl  # pip install dalaran-sdk

dl.init("dalaran_example_descriptors_builtin_component")
dl.spawn()

dl.log(
    "data",
    [
        dl.components.Position3DBatch([1, 2, 3]).described(
            dl.ComponentDescriptor(
                "user.CustomPoints3D:points",
                archetype="user.CustomPoints3D",
                component_type="dalaran.components.Position3D",
            )
        )
    ],
    static=True,
)

# The tags are indirectly checked by the Rust version (have a look over there
# for more info).
