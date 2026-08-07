from __future__ import annotations

import pytest
import dalaran as dl
import dalaran.blueprint as dlb


def test_background_construction() -> None:
    dl.set_strict_mode(True)

    assert dlb.Background((1.0, 0.0, 0.0)) == dlb.Background(color=(1.0, 0.0, 0.0), kind=dlb.BackgroundKind.SolidColor)
    assert dlb.Background(dlb.BackgroundKind.GradientBright) == dlb.Background(
        color=None,
        kind=dlb.BackgroundKind.GradientBright,
    )

    with pytest.raises(ValueError):
        dlb.Background(dlb.BackgroundKind.GradientBright, kind=dlb.BackgroundKind.GradientDark)
    with pytest.raises(ValueError):
        dlb.Background(dlb.BackgroundKind.GradientBright, color=(0.0, 1.0, 0.0))
    with pytest.raises(ValueError):
        dlb.Background((1.0, 0.0, 0.0), kind=dlb.BackgroundKind.GradientDark)
    with pytest.raises(ValueError):
        dlb.Background((1.0, 0.0, 0.0), color=(0.0, 1.0, 0.0))
