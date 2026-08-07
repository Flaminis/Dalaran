<!--[metadata]
title = "Clock"
description = "An analog clock built from `Boxes3D`, `Points3D`, and `Arrows3D` primitives, animated along a Dalaran timeline."
tags = ["3D", "API example"]
thumbnail = "https://static.rerun.io/clock/8c49e25f5cac4d6a1d7d0490b14cf6881bdb707b/480w.png"
thumbnail_dimensions = [480, 480]
-->


<picture>
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/clock/05e69dc20c9a28005f1ffe7f0f2ac9eeaa95ba3b/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/clock/05e69dc20c9a28005f1ffe7f0f2ac9eeaa95ba3b/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/clock/05e69dc20c9a28005f1ffe7f0f2ac9eeaa95ba3b/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/clock/05e69dc20c9a28005f1ffe7f0f2ac9eeaa95ba3b/1200w.png">
  <img src="https://static.rerun.io/clock/05e69dc20c9a28005f1ffe7f0f2ac9eeaa95ba3b/full.png" alt="Clock example screenshot">
</picture>

An example visualizing an analog clock with hour, minute and seconds hands using Dalaran Arrow3D primitives.

## Used Dalaran types

[`Boxes3D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes3d), [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d), [`Arrows3D`](https://www.dalaran.dev/docs/reference/types/archetypes/arrows3d)

## Logging and visualizing with Dalaran

The visualizations in this example were created with the following Dalaran code:

The clock's frame is logged as a 3D box using [`Boxes3D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes3d) archetype.
 ```python
dl.log(
    "world/frame",
    dl.Boxes3D(half_sizes=[LENGTH_S, LENGTH_S, 1.0], centers=[0.0, 0.0, 0.0]),
    static=True,
)
 ```

Then, the positions and colors of points and arrows representing the hands of a clock for seconds, minutes, and hours are logged in each simulation time.
It first sets the simulation time using [`timelines`](https://www.dalaran.dev/docs/concepts/logging-and-ingestion/timelines), calculates the data for each hand, and logs it using [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d) and [`Arrows3D`](https://www.dalaran.dev/docs/reference/types/archetypes/arrows3d) archetypes.
This enables the visualization of the clock's movement over time.

 ```python
for step in range(steps):
    dl.set_time("sim_time", duration=t_secs)

    # … calculating seconds …
    dl.log("world/seconds_pt", dl.Points3D(positions=point_s, colors=color_s))
    dl.log("world/seconds_hand", dl.Arrows3D(vectors=point_s, colors=color_s, radii=WIDTH_S))

    # … calculating minutes …
    dl.log("world/minutes_pt", dl.Points3D(positions=point_m, colors=color_m))
    dl.log("world/minutes_hand", dl.Arrows3D(vectors=point_m, colors=color_m, radii=WIDTH_M))

    # … calculating hours …
    dl.log("world/hours_pt", dl.Points3D(positions=point_h, colors=color_h))
    dl.log("world/hours_hand", dl.Arrows3D(vectors=point_h, colors=color_h, radii=WIDTH_H))
 ```

## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/clock
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m clock  # run the example
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python -m clock --help
```
