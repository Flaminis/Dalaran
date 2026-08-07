"""Log line strips over time and view a sliding window (e.g. trajectories)."""

import math

import dalaran as dl
import dalaran.blueprint as dlb


def point(t: float, phase: float) -> list[float]:
    # Sample a point on a helix.
    angle = 0.5 * t + phase
    return [math.cos(angle), math.sin(angle), 0.1 * t]


dl.init("dalaran_example_line_strips3d_time_window", spawn=True)

# Configure the visible time range in the blueprint.
# You can also override this per entity.
dl.send_blueprint(
    dlb.Spatial3DView(
        origin="/",
        time_ranges=dlb.VisibleTimeRange(
            "time",
            start=dlb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
            end=dlb.TimeRangeBoundary.cursor_relative(),
        ),
    )
)

# Log the line strip increments with timestamps.
for i in range(600):
    t0 = i / 30.0
    t1 = (i + 1) / 30.0

    dl.set_time("time", duration=t1)
    dl.log(
        "trails",
        dl.LineStrips3D(
            [
                [point(t0, 0.0), point(t1, 0.0)],
                [point(t0, math.pi), point(t1, math.pi)],
            ],
            colors=[[255, 120, 0], [0, 180, 255]],
            radii=0.02,
        ),
    )
