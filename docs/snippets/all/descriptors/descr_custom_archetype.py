#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dalaran as dl  # pip install dalaran-sdk

if TYPE_CHECKING:
    import numpy.typing as npt


class CustomPoints3D(dl.AsComponents):  # type: ignore[misc]
    def __init__(
        self: Any, positions: npt.ArrayLike, colors: npt.ArrayLike
    ) -> None:
        self.positions = dl.components.Position3DBatch(positions).described(
            dl.ComponentDescriptor(
                "user.CustomPoints3D:custom_positions",
                archetype="user.CustomPoints3D",
                component_type="user.CustomPosition3D",
            ),
        )
        self.colors = dl.components.ColorBatch(colors).described(
            dl.ComponentDescriptor("user.CustomPoints3D:colors").with_overrides(
                archetype="user.CustomPoints3D",
                component_type=dl.components.ColorBatch._COMPONENT_TYPE,
            )
        )

    def as_component_batches(self) -> list[dl.DescribedComponentBatch]:
        return [self.positions, self.colors]


dl.init("dalaran_example_descriptors_custom_archetype")
dl.spawn()

dl.log("data", CustomPoints3D([[1, 2, 3]], [0xFF00FFFF]), static=True)

# The tags are indirectly checked by the Rust version (have a look over there
# for more info).
