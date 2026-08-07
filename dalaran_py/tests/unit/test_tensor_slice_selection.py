from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, cast

import dalaran as dl
import dalaran.blueprint as dlb
import numpy as np

from .common_arrays import none_empty_or_value

if TYPE_CHECKING:
    from dalaran.blueprint.datatypes import TensorDimensionIndexSliderArrayLike


def test_tensor_slice_selection() -> None:
    widths = [
        None,
        2,
        dl.datatypes.TensorDimensionSelection(dimension=2, invert=False),
        dl.components.TensorWidthDimension(dimension=2, invert=False),
    ]
    heights = [
        None,
        3,
        dl.datatypes.TensorDimensionSelection(dimension=3, invert=False),
        dl.components.TensorHeightDimension(dimension=3, invert=False),
    ]
    indices_arrays = [
        [
            dl.components.TensorDimensionIndexSelection(dimension=1, index=3),
            dl.components.TensorDimensionIndexSelection(dimension=2, index=2),
            dl.components.TensorDimensionIndexSelection(dimension=3, index=1),
        ],
        None,
    ]
    slider_arrays = [
        None,
        [1, 2, 3],
        [
            dlb.components.TensorDimensionIndexSlider(1),
            dlb.components.TensorDimensionIndexSlider(2),
            dlb.components.TensorDimensionIndexSlider(3),
        ],
        np.array([1, 2, 3]),
    ]

    all_arrays = itertools.zip_longest(
        widths,
        heights,
        indices_arrays,
        slider_arrays,
    )

    for width, height, indices, slider in all_arrays:
        width = cast("dl.datatypes.TensorDimensionSelectionLike | None", width)
        height = cast("dl.datatypes.TensorDimensionSelectionLike | None", height)
        indices = cast("dl.datatypes.TensorDimensionIndexSelectionArrayLike | None", indices)
        slider = cast("TensorDimensionIndexSliderArrayLike | None", slider)

        print(
            f"dl.TensorSliceSelection(\n"
            f"    width={width!r}\n"
            f"    height={height!r}\n"
            f"    indices={indices!r}\n"
            f"    slider={slider!r}\n"
            f")",
        )
        arch = dlb.TensorSliceSelection(
            width=width,
            height=height,
            indices=indices,
            slider=slider,
        )
        print(f"{arch}\n")

        assert arch.width == dl.components.TensorWidthDimensionBatch._converter(
            none_empty_or_value(width, dl.components.TensorWidthDimension(dimension=2, invert=False)),
        )
        assert arch.height == dl.components.TensorHeightDimensionBatch._converter(
            none_empty_or_value(height, dl.components.TensorHeightDimension(dimension=3, invert=False)),
        )
        assert arch.indices == dl.components.TensorDimensionIndexSelectionBatch._converter(
            none_empty_or_value(indices, indices_arrays[0]),
        )
        assert arch.slider == dlb.components.TensorDimensionIndexSliderBatch._converter(
            none_empty_or_value(slider, [1, 2, 3]),
        )
