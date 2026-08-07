from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dalaran.components as rrc
import dalaran.datatypes as dlr
from dalaran.archetypes import ViewCoordinates

from .common_arrays import none_empty_or_value

if TYPE_CHECKING:
    from dalaran.datatypes.view_coordinates import ViewCoordinatesArrayLike


def view_coordinates_expected(obj: Any) -> rrc.ViewCoordinatesBatch:
    expected = none_empty_or_value(
        obj,
        [dlr.ViewDir.Right, dlr.ViewDir.Down, dlr.ViewDir.Forward],
    )

    return rrc.ViewCoordinatesBatch(expected)


assert rrc.ViewCoordinates.ViewDir is dlr.ViewDir


VIEW_COORDINATES_INPUTS: list[ViewCoordinatesArrayLike] = [
    rrc.ViewCoordinates([
        dlr.ViewDir.Right,
        dlr.ViewDir.Down,
        dlr.ViewDir.Forward,
    ]),
    [
        dlr.ViewDir.Right,
        dlr.ViewDir.Down,
        dlr.ViewDir.Forward,
    ],
    rrc.ViewCoordinates.RDF,
    [rrc.ViewCoordinates.RDF],
]


def test_view_coordinates() -> None:
    for coordinates in VIEW_COORDINATES_INPUTS:
        # TODO(jleibs): Figure out why mypy is confused by this arg-type
        arch = ViewCoordinates(coordinates)  # type: ignore[arg-type]

        print(f"dl.ViewCoordinates(\n    {coordinates!s}\n)")
        print(f"{arch}\n")

        assert arch.xyz == view_coordinates_expected(coordinates)
