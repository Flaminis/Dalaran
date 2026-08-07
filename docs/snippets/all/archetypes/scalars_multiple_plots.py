"""Log a scalar over time."""

from math import cos, sin, tau

import numpy as np

import dalaran as dl

dl.init("dalaran_example_scalar_multiple_plots", spawn=True)
lcg_state = np.int64(0)

# Set up plot styling:
# They are logged as static as they don't change over time and apply to
# all timelines.
# Log two lines series under a shared root so that they show in the same
# plot by default.
dl.log(
    "trig/sin",
    dl.SeriesLines(colors=[255, 0, 0], names="sin(0.01t)"),
    static=True,
)
dl.log(
    "trig/cos",
    dl.SeriesLines(colors=[0, 255, 0], names="cos(0.01t)"),
    static=True,
)


# NOTE: `SeriesLines` and `SeriesPoints` can both be logged without any
#       associated data (all fields are optional). In `v0.24` we removed
#       indicators, which now results in no data logged at all, when no
#       fields are specified. Therefore, we log a circle shape as a
#       marker if no arguments are supplied.
#       More information: https://github.com/rerun-io/rerun/issues/10512

# Log scattered points under a different root so that they show in a
# different plot by default.
dl.log("scatter/lcg", dl.SeriesPoints(), static=True)

# Log the data on a timeline called "step".
for t in range(int(tau * 2 * 100.0)):
    dl.set_time("step", sequence=t)

    dl.log("trig/sin", dl.Scalars(sin(float(t) / 100.0)))
    dl.log("trig/cos", dl.Scalars(cos(float(t) / 100.0)))

    # simple linear congruency generator
    lcg_state = (1140671485 * lcg_state + 128201163) % 16777216
    dl.log("scatter/lcg", dl.Scalars(lcg_state.astype(np.float64)))
