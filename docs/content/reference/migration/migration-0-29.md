---
title: Migrating from 0.28 to 0.29
order: 981
hidden: true
---

<!--   ^^^ this number must be _decremented_ when you copy/paste this file -->

## 🐍 Python API
### New API for defining visualizer overrides

The Python API for setting blueprint overrides now uses special visualizer objects under the hood.
A sideffect of that is that `VisualizerOverrides` no longer exists, instead you just list the visualizers out:


Before:
```py
dl.send_blueprint(
    dlb.TimeSeriesView(
        overrides={
            "trig/sin": [
                dlb.VisualizerOverrides([dlb.visualizers.SeriesLines, dlb.visualizers.SeriesPoints]),
            ],
        },
    )
)
```
After:
```py
dl.send_blueprint(dlb.TimeSeriesView(overrides={"trig/sin": [dl.SeriesLines(), dl.SeriesPoints()]}))
```

In general, you can now pass any archetype that has a corresponding visualizer.
Internally, passing such a `VisualizableArchetype` is a shorthand for calling `.visualizer()` on the object.

### `Entry.update()` is deprecated in favor of `Entry.set_name()`

The `Entry.update()` method has been deprecated. Use `Entry.set_name()` instead for renaming entries.

```python
# Before (deprecated)
entry.update(name="new_name")

# After
entry.set_name("new_name")
```

The deprecated method will emit a `DeprecationWarning` and will be removed in a future release.

### `CatalogClient`: Renamed `addr` constructor parameter
The first argument to `CatalogClient` is now called `url`.
The other arguments (including `token`) are now kw-args.

### `Server`: Renamed `addr` constructor parameter
The first argument to `Server` is now called `host`.

### Deprecated `dalaran.dataframe` API has been removed

The `dalaran.dataframe` module and its associated APIs, which were deprecated in 0.28, have now been fully removed. This includes `RecordingView`, `Recording.view()`, and the ability to run dataframe queries locally via this module.

Please refer to the [0.28 migration guide section on `RecordingView` and local dataframe API](migration-0-28.md#recordingview-and-local-dataframe-api-deprecated) for details on updating your code to use `dalaran.server.Server` and the `dalaran.catalog` API instead.

### Deprecated `dalaran.catalog` APIs have been removed

The deprecated `dalaran.catalog` APIs that were marked for removal in 0.28 have now been fully removed. If you were using any of these deprecated methods, you must update your code to use the new APIs.

Please refer to the [0.28 migration guide section on catalog API overhaul](migration-0-28.md#python-sdk-catalog-api-overhaul) for more details on the new API patterns.

### Multiple internal submodules were move to properly mark internal
Most of their functionality is already exposed indirectly through re-exports.
If you still need to use any functionality directly you can still find them in their new location.
* `dl.color_conversion` -> `dl._color_conversion`
* `dl.event` -> `dl._event`
* `dl.legacy_notebook` -> `dl._legacy_notebook`
* `dl.logging_handler` -> `dl._logging_handler`
* `dl.memory` -> `dl._memory`
* `dl.script_helpers` -> `dl._script_helpers`

## CLI
`dalaran server --addr …` has been renamed `dalaran server --host …`

## Overrides in blueprint files can't be imported

Dalaran 0.29 cannot currently load component overrides from `.rbl` files created in previous versions. Support for legacy overrides is coming soon.

## Dataset re-registration required to fix missing `name` and `start_time` in segment table

This release fixes a bug where the built-in properties ([`RecordingInfo`](../types/archetypes/recording_info.md), including `name` and `start_time`) would not be displayed in the segment table. On catalog server deployments, property extraction happens at registration time. This means that datasets will need to be re-registered for these columns to be populated.

The OSS server is not affected because it generates the segment table on the fly.
