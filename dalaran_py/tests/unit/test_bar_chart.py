from __future__ import annotations

import dalaran as dl
import numpy as np
import pytest


def test_bar_chart_shapes() -> None:
    """`BarChart` accepts only 1D data."""
    dl.set_strict_mode(True)

    # Single-element 1D array.
    dl.BarChart(np.array([1.0]))
    # Regular 1D array.
    dl.BarChart(np.array([1.0, 2.0, 3.0]))
    # Leading singleton dimension.
    dl.BarChart(np.array([[1.0, 2.0, 3.0]]))

    with pytest.raises(ValueError, match="Bar chart data should only be 1D"):
        dl.BarChart(np.array(1.0))

    with pytest.raises(ValueError, match="Bar chart data should only be 1D"):
        dl.BarChart(np.ones((2, 2)))
