"""Use a blueprint to customize a map view."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_map_view", spawn=True)

dl.log(
    "points",
    dl.GeoPoints(
        lat_lon=[[47.6344, 19.1397], [47.6334, 19.1399]],
        radii=dl.Radius.ui_points(20.0),
    ),
)

# Create a map view to display the chart.
blueprint = dlb.Blueprint(
    dlb.MapView(
        origin="points",
        name="MapView",
        zoom=16.0,
        background=dlb.MapProvider.OpenStreetMap,
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
