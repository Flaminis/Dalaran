from __future__ import annotations

import dalaran.blueprint as dlb

from .blueprint_utils import assert_blueprint_contents_are_equal


def test_map_view_blueprint() -> None:
    """Various ways to create a `MapView` blueprint."""

    bp1 = dlb.MapView(origin="point", name="MapView", zoom=16, background="openstreetmap")
    bp2 = dlb.MapView(origin="point", name="MapView", zoom=dlb.components.ZoomLevel(16), background="openstreetmap")
    bp3 = dlb.MapView(
        origin="point",
        name="MapView",
        zoom=dlb.archetypes.MapZoom(16),
        background=dlb.MapProvider.OpenStreetMap,
    )
    bp4 = dlb.MapView(
        origin="point",
        name="MapView",
        zoom=dlb.archetypes.MapZoom(dlb.components.ZoomLevel(16)),
        background=dlb.archetypes.MapBackground(dlb.MapProvider.OpenStreetMap),
    )

    # assert bp1 == bp2 == bp3 == bp4
    assert_blueprint_contents_are_equal(bp1, bp2, bp3, bp4)
