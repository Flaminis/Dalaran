from __future__ import annotations

import dalaran as dl


def test_log_point2d_basic() -> None:
    """Basic test: logging a point shouldn't raise an exception."""
    points = dl.Points2D([(0, 0), (2, 2), (2, 2.5), (2.5, 2), (3, 4)], radii=0.5)
    dl.init("dalaran_example_test_log")
    dl.log("points", points)
