"""Log a scalar over time and override the visualizer."""

from math import cos, sin, tau

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_series_line_overrides", spawn=True)

# Log the data on a timeline called "step".
for t in range(int(tau * 2 * 10.0)):
    dl.set_time("step", sequence=t)

    dl.log("trig/sin", dl.Scalars(sin(float(t) / 10.0)))
    dl.log("trig/cos", dl.Scalars(cos(float(t) / 10.0)))

# Use the SeriesPoints visualizer for the sin series.
dl.send_blueprint(
    dlb.TimeSeriesView(
        overrides={
            "trig/sin": [dl.SeriesLines(), dl.SeriesPoints()],
        },
    ),
)
