---
title: Migrating from 0.22 to 0.23
order: 987
hidden: true
---

## Reserved namespaces
Starting with this release, the SDKs will log Dalaran-related information to reserved entity path namespaces that are prefixed with `__`.
Most notably, there is `__warnings/`, which used to be called `dalaran/` and can be used to log exceptions that occurred in the SDKs.
We also introduced `__properties/`, which stores recording-level information that is logged via the new `set_property` methods in the SDKs.
Reserved namespaces are highlighted with a ⚙️ icon in the viewer UI.

## Timelines are uniquely identified by name
Previously, you could (confusingly) have two timelines with the same name, as long as they had different types (sequence vs temporal).
This is no longer possible.
Timelines are now uniquely identified by name, and if you use different types on the same timeline, you will get a logged warning, and the _latest_ type will be used to interpret the full set of time data.

## Unify the names of time units
We have been wildly inconsistent with how we name our time units, and it is time we fixed it. So starting now, we're using:

* `secs` instead of `s` or `seconds`
* `nanos` instead of `ns` or `nanoseconds`
* `millis` instead of `ms` or `milliseconds`

All function and parameters using the old names have been deprecated, and will be removed in a future version.

##### Why these names?
* They are short without being cryptic
* They are the ones the Rust standard library (mostly) use: https://doc.rust-lang.org/stable/std/time/struct.Duration.html
* Anything is better than being inconsistent :)

## Differentiate between timestamps and durations
We've added a explicit API for setting time, where you need to explicitly specify if a time is either a timestamp (e.g. `2025-03-03T14:34:56.123456789`) or a duration (e.g. `123s`).

Before, Dalaran would try to guess what you meant (small values were assumed to be durations, and large values were assumes to be durations since the Unix epoch, i.e. timestamps).
Now you need to be explicit.


### 🦀 Rust: deprecated `RecordingStream::set_time_secs` and `set_time_nanos`
Use one of these instead:
* `set_duration_secs`
* `set_timestamp_secs_since_epoch`
* `set_time` with `std::time::Duration`
* `set_time` with `std::time::SystemTime`


### 🌊 C++
We've deprecated the following functions, with the following replacements:
* `set_time` -> `set_time_duration` or `set_time_timestamp`
* `set_time_seconds` -> `set_time_duration_secs` or `set_time_timestamp_secs_since_epoch`
* `set_time_nanos` -> `set_time_duration_nanos` or `set_time_timestamp_nanos_since_epoch`

`TimeColumn` also has deprecated functions.


### 🐍 Python: replaced `dl.set_time_*` functions with a single `dl.set_time`
We've deprecated `dl.set_time_secs`, `dl.set_time_nanos`, as well as `dl.set_time_sequence` and replaced them with `dl.set_time`.
`set_time` takes either a `sequence=`, `duration=` or `timestamp=` argument.

`duration` must be either:
* seconds as `int` or `float`
* [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta)
* [`numpy.timedelta64`](https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.timedelta64)

`timestamp` must be either:
* seconds since unix epoch (1970-01-01) as `int` or `float`
* [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime)
* [`numpy.datetime64`](https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.datetime64)

#### Migrating
##### `dl.set_sequence("foo", 42)`
New: `dl.set_time("foo", sequence=42)`

##### `dl.set_time_secs("foo", duration_secs)`
When using relative times (durations/timedeltas): `dl.set_time("foo", duration=duration_secs)`
You can also pass in a [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta) or [`numpy.timedelta64`](https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.timedelta64) directly.

##### `dl.set_time_secs("foo", seconds_since_epoch)`
New: `dl.set_time("foo", timestamp=seconds_since_epoch)`
You can also pass in a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime) or [`numpy.datetime64`](https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.datetime64) directly.

##### `dl.set_time_nanos("foo", duration_nanos)`
Either:
* `dl.set_time("foo", duration=1e-9 * duration_nanos)`
* `dl.set_time("foo", duration=np.timedelta64(duration_nanos, 'ns'))`

The former is subject to (double-precision) floating point precision loss (but still nanosecond precision for timedeltas below less than 100 days in duration), while the latter is lossless.

##### `dl.set_time_nanos("foo", nanos_since_epoch)`
Either:
* `dl.set_time("foo", timestamp=1e-9 * nanos_since_epoch)`
* `dl.set_time("foo", timestamp=np.datetime64(nanos_since_epoch, 'ns'))`

The former is subject to (double-precision) floating point precision loss (still microsecond precision for the next century), while the latter is lossless.


### 🐍 Python: replaced `dl.Time*Column` with `dl.TimeColumn`
Similarly to the above new `set_time` API, there is also a new `TimeColumn` class that replaces `TimeSequenceColumn`, `TimeSecondsColumn`, and `TimeNanosColumn`.
The migration is very similar to the above.

#### Migration
##### `dl.TimeSequenceColumn("foo", values)`
New: `dl.TimeColumn("foo", sequence=values)`

##### `dl.TimeSecondsColumn("foo", duration_secs)`
New: `dl.TimeColumn("foo", duration=duration_secs)`

##### `dl.TimeSecondsColumn("foo", seconds_since_epoch)`
New: `dl.TimeColumn("foo", timestamp=seconds_since_epoch)`

##### `dl.TimeNanosColumn("foo", duration_nanos)`
Either:
* `dl.TimeColumn("foo", duration=1e-9 * duration_nanos)`
* `dl.TimeColumn("foo", duration=np.timedelta64(duration_nanos, 'ns'))`

The former is subject to (double-precision) floating point precision loss (but still nanosecond precision for timedeltas below less than 100 days in duration), while the latter is lossless.

##### `dl.TimeNanosColumn("foo", nanos_since_epoch)`
Either:
* `dl.TimeColumn("foo", duration=1e-9 * nanos_since_epoch)`
* `dl.TimeColumn("foo", duration=np.timedelta64(nanos_since_epoch, 'ns'))`

The former is subject to (double-precision) floating point precision loss (still microsecond precision for the next century), while the latter is lossless.


### Dataloader time arguments
The CLI API for external dataloaders has changed the following argument names:

* `--sequence` -> `--time_sequence`
* `--time` -> `--time_duration_nanos` or `--time_timestamp_nanos`


## 🐍 Python: `dl.new_recording` is now deprecated in favor of `dl.RecordingStream`

Previously, `RecordingStream` instances could be created with the `dl.new_recording()` function. This method is now deprecated in favor of directly using the [`RecordingStream`](https://ref.dalaran.dev/docs/python/0.23.0/common/initialization_functions/#dalaran.RecordingStream) constructor. The `RecordingStream` constructor is mostly backward compatible, so in most case it is matter of using `RecordingStream` instead of `new_recording`:

<!-- NOLINT_START -->

```python
# before
rec = dl.new_recording("dalaran_example")

# after
rec = dl.RecordingStream("my_app_id")
```

If you used the `spawn=True` argument, you will now have to call the `spawn()` method explicitly:

```python
# before
rec = dl.new_recording("my_app_id", spawn=True)

# after
rec = dl.RecordingStream("my_app_id")
rec.spawn()
```

<!-- NOLINT_END -->

## 🐍 Python: removed `dl.log_components()`, `dl.connect()`, `dl.connect_tcp()`, and `dl.serve()`

These functions were [deprecated](migration-0-22.md#python-api-changes) in 0.22 and are no longer available.

Calls to `dl.log_components()` API are now superseded by the new partial update API. See the [documentation](../../concepts/logging-and-ingestion/latest-at.md#partial-updates) and the [migration instructions](migration-0-22.md#partial-updates).

Calls to `dl.connect()` and `dl.connect_tcp()` must be changed to [`dl.connect_grpc()`](https://ref.dalaran.dev/docs/python/0.23.0/common/initialization_functions/#dalaran.connect_grpc).

Calls to `dl.serve()` must be changed to [`dl.serve_web()`](https://ref.dalaran.dev/docs/python/0.23.0/common/initialization_functions/#dalaran.serve_web).

## 🌊 C++: removed `connect` and `connect_tcp` from `RecordingStream`

Calls to these functions must be changed to `connect_grpc`. Note that the string passed to `connect_grpc` must now be a valid Dalaran URL. If you were previously calling `connect_grpc("127.0.0.1:9876")`, it must be changed to `connect_grpc("dalaran+http://127.0.0.1:9876/proxy")`.

See the [`RecordingStream` docs](https://ref.dalaran.dev/docs/cpp/0.23.0/classdalaran_1_1RecordingStream.html) for more information.

## 🦀 Rust: removed `connect` and `connect_tcp` from `RecordingStream` and `RecordingStreamBuilder`

Calls to these functions must be changed to use [`connect_grpc`](https://docs.rs/dalaran/0.23.0/dalaran/struct.RecordingStreamBuilder.html#method.connect_grpc) instead.

Note that the string passed to `connect_grpc` must now be a valid Dalaran URL. If you were previously calling `connect("127.0.0.1:9876")`, it must be changed to `connect_grpc("dalaran+http://127.0.0.1:9876/proxy")`.

The following schemes are supported: `dalaran+http://`, `dalaran+https://` and `dalaran://`, which is an alias for `dalaran+https://`.
These schemes are then converted on the fly to either `http://` or `https://`.
Dalaran uses gRPC-based protocols under the hood, which means that the paths (`/catalog`, `/recording/12345`, …) are mapped to gRPC services and methods on the fly.

## 🐍 Python: blueprint overrides & defaults are now archetype based

Just like with `send_columns` in the previous release, blueprint overrides and defaults are now archetype based.

**Examples:**

Setting default & override for radius

Before:
```python
dlb.Spatial2DView(
    name="Rect 1",
    origin="/",
    contents=["/**"],
    defaults=[dl.components.Radius(2)],
    overrides={"rect/0": [dl.components.Radius(1)]},
)
```
After:
```python
dlb.Spatial2DView(
    name="Rect 1",
    origin="/",
    contents=["/**"],
    defaults=[dl.Boxes2D.from_fields(radii=1)],
    overrides={"rect/0": dl.Boxes2D.from_fields(radii=2)},
)
```

Setting up styles for a plot.

Before:
```python
# …
(
    dlb.TimeSeriesView(
        name="Trig",
        origin="/trig",
        overrides={
            "/trig/sin": [dl.components.Color([255, 0, 0]), dl.components.Name("sin(0.01t)")],
            "/trig/cos": [dl.components.Color([0, 255, 0]), dl.components.Name("cos(0.01t)")],
        },
    ),
)
(
    dlb.TimeSeriesView(
        name="Classification",
        origin="/classification",
        overrides={
            "classification/line": [dl.components.Color([255, 255, 0]), dl.components.StrokeWidth(3.0)],
            "classification/samples": [
                dlb.VisualizerOverrides("SeriesPoints")
            ],  # This ensures that the `SeriesPoints` visualizers is used for this entity.
        },
    ),
)
# …
```
After:
```python
# …
(
    dlb.TimeSeriesView(
        name="Trig",
        origin="/trig",
        overrides={
            "/trig/sin": dl.SeriesLines.from_fields(colors=[255, 0, 0], names="sin(0.01t)"),
            "/trig/cos": dl.SeriesLines.from_fields(colors=[0, 255, 0], names="cos(0.01t)"),
        },
    ),
)
(
    dlb.TimeSeriesView(
        name="Classification",
        origin="/classification",
        overrides={
            "classification/line": dl.SeriesLines.from_fields(colors=[255, 255, 0], widths=3.0),
            "classification/samples": dlb.VisualizerOverrides(
                "SeriesPoints"
            ),  # This ensures that the `SeriesPoints` visualizers is used for this entity.
        },
    ),
)
# …
```

> [!WARNING]
> Just like regular log/send calls, overlapping component types still overwrite each other.
> E.g. overriding a box radius will also override point radius on the same entity.
> In a future release, components tagged with a different archetype or field name can live side by side,
> but for the moment the Viewer is not able to make this distinction.
> For details see [#6889](https://github.com/rerun-io/rerun/issues/6889).


### Overriding `Visible` and `Interactive` is now always recursive

Previously, it was possible to override visibility individually, but not recursively.
Also, Viewer interaction [was hampered](https://github.com/rerun-io/rerun/issues/9254) by this.

Overrides for these two properties are now always recursive, and can be applied using the new `EntityBehavior` archetype.

Before:
```python
dl.send_blueprint(
    dlb.Spatial2DView(
        overrides={"points": [dlb.components.Visible(False)]}
        overrides={
            "hidden_subtree": [dlb.components.Visible(False)],
            "hidden_subtree/child0": [dlb.components.Visible(False)],
            "hidden_subtree/child1": [dlb.components.Visible(False)],
            # …
            "non_interactive_subtree": [dlb.components.Interactive(False)],
            "non_interactive_subtree/child0": [dlb.components.Interactive(False)],
            "non_interactive_subtree/child1": [dlb.components.Interactive(False)],
            # …
        }
    ),
)
```

After:
```python
dl.send_blueprint(
    dlb.Spatial2DView(
        overrides={
            "hidden_subtree": dlb.EntityBehavior(visible=False),
            "hidden_subtree/not_hidden": dlb.EntityBehavior(visible=True),
            "non_interactive_subtree": dlb.EntityBehavior(interactive=False),
        }
    )
)
```

### Visible time range overrides have to specify the underlying archetype

(Note that this functionality broken in at least Dalaran 0.21 and 0.22 but is fixed now. See [#8557](https://github.com/rerun-io/rerun/issues/8557))

Before:
```python
# …
overrides = (
    {
        "helix/structure/scaffolding/beads": [
            dlb.VisibleTimeRange(
                "stable_time",
                start=dlb.TimeRangeBoundary.cursor_relative(seconds=-0.3),
                end=dlb.TimeRangeBoundary.cursor_relative(seconds=0.3),
            ),
        ],
    },
)
# …
```

After:
```python
# …
overrides = {
    "helix/structure/scaffolding/beads": dlb.VisibleTimeRanges(
        timeline="stable_time",
        start=dlb.TimeRangeBoundary.cursor_relative(seconds=-0.3),
        end=dlb.TimeRangeBoundary.cursor_relative(seconds=0.3),
    ),
}
# …
```
… or respectively for multiple timelines:
```python
# …
overrides = {
    "helix/structure/scaffolding/beads": dlb.VisibleTimeRanges([
        dlb.VisibleTimeRange(
            timeline="stable_time",
            start=dlb.TimeRangeBoundary.cursor_relative(seconds=-0.3),
            end=dlb.TimeRangeBoundary.cursor_relative(seconds=0.3),
        ),
        dlb.VisibleTimeRange(
            timeline="index", start=dlb.TimeRangeBoundary.absolute(seq=10), end=dlb.TimeRangeBoundary.absolute(seq=100)
        ),
    ])
}
# …
```

## Types for time series plots are now plural

The `Scalar`/`SeriesPoints`/`SeriesLines` archetypess have been deprecated in favor of
`Scalars`/`SeriesPoints`/`SeriesLines` since you can now have a multiple
scatter plots or lines on the same archetype.


Before:
```python
dl.log("trig/sin", dl.SeriesLines(color=[s0, 255, 0], name="cos(0.01t)", width=4), static=True)

for t in range(int(tau * 2 * 100.0)):
    dl.set_time("step", sequence=t)
    dl.log("trig/sin", dl.Scalar(sin(float(t) / 100.0)))
```

After:
```python
dl.log("trig/sin", dl.SeriesLines(colors=[255, 0, 0], names="sin(0.01t)", widths=2), static=True)

for t in range(int(tau * 2 * 100.0)):
    dl.set_time("step", sequence=t)
    dl.log("trig/sin", dl.Scalars(sin(float(t) / 100.0)))
```
<!-- This is trivial enough across languages why I left it at a python only example -->

The old types still work for the moment but will be removed in a future release.

## Consistent constructor naming of `Asset3D` across C++ and Rust

We've deprecated inconsistent constructors with following replacements:
- 🦀 Rust: `from_file` -> `from_file_path`
- 🌊 C++:
    - `from_file` -> `from_file_path`
    - `from_bytes` -> `from_file_contents`

## Jupyter notebooks

### Explicit `Viewer` imports

We've removed `notebook` from the root `dalaran` namespace. `Viewer` must now be imported directly:

Before:
```python
viewer = dl.notebook.Viewer()
viewer.display()
```

After:
```python
from dalaran.notebook import Viewer

viewer = Viewer()
viewer.display()
```

`dl.notebook_show` is still available in the root `dalaran` namespace.
