"""Log a simple geospatial line string."""

import dalaran as dl

dl.init("dalaran_example_geo_line_strings", spawn=True)

dl.log(
    "colorado",
    dl.GeoLineStrings(
        lat_lon=[
            [41.0000, -109.0452],
            [41.0000, -102.0415],
            [36.9931, -102.0415],
            [36.9931, -109.0452],
            [41.0000, -109.0452],
        ],
        radii=dl.Radius.ui_points(2.0),
        colors=[0, 0, 255],
    ),
)
