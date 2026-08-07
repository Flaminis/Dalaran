"""Shows how to implement custom archetypes and components."""

from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import numpy.typing as npt
import pyarrow as pa

import dalaran as dl


class ConfidenceBatch(dl.ComponentBatchMixin):  # type: ignore[misc]
    """A batch of confidence data."""

    def __init__(self: Any, confidence: npt.ArrayLike) -> None:
        self.confidence = confidence

    def as_arrow_array(self) -> pa.Array:
        """The arrow batch representing the custom component."""
        return pa.array(self.confidence, type=pa.float32())


class CustomPoints3D(dl.AsComponents):  # type: ignore[misc]
    """A custom archetype extending the builtin `Points3D` with extra data."""

    def __init__(
        self: Any, positions: npt.ArrayLike, confidences: npt.ArrayLike
    ) -> None:
        self.points3d = dl.Points3D(positions)
        self.confidences = ConfidenceBatch(confidences).described(
            dl.ComponentDescriptor(
                "user.CustomPoints3D:confidences",
                archetype="user.CustomPoints3D",
                component_type="user.Confidence",
            )
        )

    def as_component_batches(self) -> list[dl.DescribedComponentBatch]:
        return [
            # The components from Points3D
            *self.points3d.as_component_batches(),
            # Custom confidence data
            self.confidences,
        ]


def log_custom_data() -> None:
    lin = np.linspace(-5, 5, 3)
    z, y, x = np.meshgrid(lin, lin, lin, indexing="ij")
    point_grid = np.vstack([x.flatten(), y.flatten(), z.flatten()]).T

    dl.log(
        "left/my_confident_point_cloud",
        CustomPoints3D(
            positions=point_grid,
            confidences=[42],
        ),
    )

    dl.log(
        "right/my_polarized_point_cloud",
        CustomPoints3D(
            positions=point_grid, confidences=np.arange(0, len(point_grid))
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Logs rich data using the Dalaran SDK."
    )
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_custom_data")
    log_custom_data()
    dl.script_teardown(args)


if __name__ == "__main__":
    main()
