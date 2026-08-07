"""Use a blueprint to customize a TimeSeriesView."""

import math

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_timeseries", spawn=True)

# Log some trigonometric functions
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
dl.log(
    "trig/cos_scaled",
    dl.SeriesLines(colors=[0, 0, 255], names="cos(0.01t) scaled"),
    static=True,
)
for t in range(int(math.pi * 4 * 100.0)):
    dl.set_time("timeline0", sequence=t)
    dl.set_time("timeline1", duration=t)
    dl.log("trig/sin", dl.Scalars(math.sin(float(t) / 100.0)))
    dl.log("trig/cos", dl.Scalars(math.cos(float(t) / 100.0)))
    dl.log("trig/cos_scaled", dl.Scalars(math.cos(float(t) / 100.0) * 2.0))

# Create a TimeSeries View
blueprint = dlb.Blueprint(
    dlb.Vertical(
        contents=[
            dlb.TimeSeriesView(
                origin="/trig",
                # Set a custom Y axis.
                axis_y=dlb.ScalarAxis(range=(-1.0, 1.0), zoom_lock=True),
                # Configure the legend.
                plot_legend=dlb.PlotLegend(visible=False),
                # Set time different time ranges for different timelines.
                time_ranges=[
                    # Sliding window depending on the time cursor for the
                    # first timeline.
                    dlb.VisibleTimeRange(
                        "timeline0",
                        start=dlb.TimeRangeBoundary.cursor_relative(seq=-100),
                        end=dlb.TimeRangeBoundary.cursor_relative(),
                    ),
                    # Time range from some point to the end of the timeline
                    # for the second timeline.
                    dlb.VisibleTimeRange(
                        "timeline1",
                        start=dlb.TimeRangeBoundary.absolute(seconds=300.0),
                        end=dlb.TimeRangeBoundary.infinite(),
                    ),
                ],
            ),
            dlb.TimeSeriesView(
                origin="/trig",
                axis_x=dlb.TimeAxis(
                    view_range=dl.TimeRange(
                        start=dlb.TimeRangeBoundary.cursor_relative(
                            seconds=-100
                        ),
                        end=dlb.TimeRangeBoundary.cursor_relative(seconds=100),
                    ),
                    zoom_lock=True,
                ),
                # Configure the legend.
                plot_legend=dlb.PlotLegend(visible=True),
                background=dlb.archetypes.PlotBackground(
                    color=[128, 128, 128], show_grid=False
                ),
            ),
        ]
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
