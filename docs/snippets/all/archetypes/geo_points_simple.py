"""Log some very simple geospatial point."""

import dalaran as dl

dl.init("dalaran_example_geo_points", spawn=True)

dl.log(
    "dalaran_hq",
    dl.GeoPoints(
        lat_lon=[59.319221, 18.075631],
        radii=dl.Radius.ui_points(10.0),
        colors=[255, 0, 0],
    ),
)
