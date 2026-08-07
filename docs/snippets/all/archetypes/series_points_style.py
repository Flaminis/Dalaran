"""Log a scalar over time."""

from math import cos, sin, tau

import dalaran as dl

dl.init("dalaran_example_series_point_style", spawn=True)

# Set up plot styling:
# They are logged as static as they don't change over time and apply to all
# timelines. Log two point series under a shared root so that they show in the
# same plot by default.
dl.log(
    "trig/sin",
    dl.SeriesPoints(
        colors=[255, 0, 0],
        names="sin(0.01t)",
        markers="circle",
        marker_sizes=4,
    ),
    static=True,
)
dl.log(
    "trig/cos",
    dl.SeriesPoints(
        colors=[0, 255, 0],
        names="cos(0.01t)",
        markers="cross",
        marker_sizes=2,
    ),
    static=True,
)


# Log the data on a timeline called "step".
for t in range(int(tau * 2 * 10.0)):
    dl.set_time("step", sequence=t)

    dl.log("trig/sin", dl.Scalars(sin(float(t) / 10.0)))
    dl.log("trig/cos", dl.Scalars(cos(float(t) / 10.0)))
