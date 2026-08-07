from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, cast

import dalaran as dl
import dalaran.blueprint as dlb
from dalaran.blueprint import components as blueprint_components

from .common_arrays import none_empty_or_value

if TYPE_CHECKING:
    from dalaran.datatypes.bool import BoolLike


def test_scalar_axis() -> None:
    dl.set_strict_mode(True)

    corners = [
        dlb.Corner2D.LeftTop,
        "lefttop",
        None,
    ]
    visible_array = [
        None,
        True,
    ]

    all_arrays = itertools.zip_longest(
        corners,
        visible_array,
    )

    for corner, visible in all_arrays:
        corner = cast("blueprint_components.Corner2DLike | None", corner)
        visible = cast("BoolLike | None", visible)

        print(
            f"dl.PlotLegend(\n    corner={corner!r}\n    visible={visible!r}\n)",
        )
        arch = dlb.PlotLegend(
            corner=corner,
            visible=visible,
        )
        print(f"{arch}\n")

        assert arch.corner == blueprint_components.Corner2DBatch._converter(
            none_empty_or_value(corner, dlb.Corner2D.LeftTop),
        )
        assert arch.visible == dl.components.VisibleBatch._converter(none_empty_or_value(visible, [True]))
