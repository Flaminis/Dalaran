from __future__ import annotations

import itertools
from typing import cast

import dalaran as dl
import dalaran.blueprint as dlb
import numpy as np

from .common_arrays import none_empty_or_value


def test_scalar_axis() -> None:
    dl.set_strict_mode(True)

    # All from 42.1337 to 1337.42, but expressed differently
    ranges = [
        (42.1337, 1337.42),
        [42.1337, 1337.42],
        np.array([42.1337, 1337.42]),
        dl.components.Range1D([42.1337, 1337.42]),
        None,
    ]
    zoom_locks = [
        True,
        False,
    ]

    all_arrays = itertools.zip_longest(
        ranges,
        zoom_locks,
    )

    for range, zoom_lock in all_arrays:
        range = cast("dl.datatypes.Range1DLike | None", range)
        zoom_lock = cast("dl.datatypes.Bool | None", zoom_lock)

        print(
            f"dl.ScalarAxis(\n    range={range!r}\n    zoom_lock={zoom_lock!r}\n)",
        )
        arch = dlb.ScalarAxis(
            range=range,
            zoom_lock=zoom_lock,
        )
        print(f"{arch}\n")

        assert arch.range == dl.components.Range1DBatch._converter(none_empty_or_value(range, [42.1337, 1337.42]))
        assert arch.zoom_lock == dlb.components.LockRangeDuringZoomBatch._converter(zoom_lock)
