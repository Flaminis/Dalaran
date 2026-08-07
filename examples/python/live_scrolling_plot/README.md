<!--[metadata]
title = "Live scrolling plot"
description = "A live scrolling plot built from a blueprint that updates each `TimeSeriesView`'s `time_ranges` as new data arrives."
tags = ["Plots", "Live"]
thumbnail = "https://static.rerun.io/live_scrolling_plot_thumbnail/73c6b11bd074af258b8d30092e15361e358d8069/480w.png"
thumbnail_dimensions = [480, 384]
-->

Visualize a live stream of several plots, scrolling horizontally to keep a fixed window of data.

<picture>
  <img src="https://static.rerun.io/live_scrolling_plot/9c9a9b3a4dd1d5e858ba58489f686b5d481cfb2e/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/live_scrolling_plot/9c9a9b3a4dd1d5e858ba58489f686b5d481cfb2e/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/live_scrolling_plot/9c9a9b3a4dd1d5e858ba58489f686b5d481cfb2e/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/live_scrolling_plot/9c9a9b3a4dd1d5e858ba58489f686b5d481cfb2e/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/live_scrolling_plot/9c9a9b3a4dd1d5e858ba58489f686b5d481cfb2e/1200w.png">
</picture>

## Used Dalaran types
[`Scalars`](https://www.dalaran.dev/docs/reference/types/archetypes/scalars)

## Setting up the blueprint

In order to only show a fixed window of data, this example creates a blueprint that uses
the `time_ranges` parameter of the `TimeSeriesView` blueprint type.

We dynamically create a `TimeSeriesView` for each plot we want to show, so that we can
set the `time_ranges`. The start of the visible time range is set to the current time
minus the window size, and the end is set to the current time.

```python
dl.send_blueprint(
    dlb.Grid(
        contents=[
            dlb.TimeSeriesView(
                origin=plot_path,
                time_ranges=[
                    dlb.VisibleTimeRange(
                        "time",
                        start=dlb.TimeRangeBoundary.cursor_relative(seconds=-args.window_size),
                        end=dlb.TimeRangeBoundary.cursor_relative(),
                    )
                ],
                plot_legend=dlb.PlotLegend(visible=False),
            )
            for plot_path in plot_paths
        ]
    ),
)
```

## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
# Setup
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/live_scrolling_plot
```

Then, simply execute the main Python script:
```bash
python -m live_scrolling_plot
```
