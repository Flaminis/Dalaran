---
title: Rerun compatibility
order: 1050
---

Dalaran shares its storage container with [Rerun](https://github.com/rerun-io/rerun), so
**existing Rerun recordings open in Dalaran as-is**, with no conversion step and no loss of
fidelity. The parts that differ are the names of things: file extensions, the protobuf
namespace, and the URI scheme.

This page spells out exactly what carries over and what does not.

## Recordings and blueprints: compatible

Dalaran renamed the file extensions, but not the file format:

| Contents  | Rerun  | Dalaran |
| --------- | ------ | ------- |
| Recording | `.rrd` | `.dlr`  |
| Blueprint | `.rbl` | `.dbl`  |

The on-disk framing is byte-for-byte the same. Files still start with the `RRF2` fourcc, followed by
the same length-delimited, Arrow-encoded messages. Dalaran keeps that fourcc on purpose: changing it
would have broken compatibility for no benefit whatsoever.

As a result, anywhere Dalaran accepts a `.dlr` or `.dbl`, it also accepts a `.rrd` or `.rbl`:

```sh
# Open an upstream Rerun recording directly in the Dalaran Viewer:
dalaran ./recording.rrd

# Stream one over HTTP:
dalaran https://example.com/recording.rrd

# Inspect or transform it with the `dlr` subcommands:
dalaran dlr print ./recording.rrd
dalaran dlr optimize ./recording.rrd -o ./recording.dlr
```

Drag-and-drop, the file-open dialog, and the web viewer's `?url=` parameter all accept the legacy
extensions too. When a legacy file is loaded, Dalaran logs a single informational line so that it is
obvious what happened:

```txt
Loaded legacy Rerun recording ./recording.rrd (.rrd); Dalaran reads these natively.
```

If you would rather normalize your archive to the Dalaran extension, `dalaran convert` will rewrite
any supported input into a single `.dlr`:

```sh
dalaran convert ./recording.rrd -o ./recording.dlr
```

Note that this is only a rename plus a re-encode of the same data; reading the original file works
just as well.

### Older Rerun versions

Recordings written by older Rerun versions (`RRF0`/`RRF1` framing, or older chunk schemas) are
migrated on read, exactly like older Dalaran recordings are. Use `dalaran dlr migrate` to write the
migrated result back to disk if you want to pay that cost only once.

## Third-party formats: compatible

Everything Rerun could ingest, Dalaran ingests: MCAP (including ROS 2 messages and Foxglove
schemas), URDF, `LeRobot` datasets, Parquet, meshes (`.glb`, `.gltf`, `.obj`, `.stl`, `.dae`), point
clouds (`.ply`), images, and MP4 video. Run `dalaran convert --list-formats` for the authoritative
list of the build you have installed.

## Not compatible

### The gRPC service namespace

Rerun's protobuf packages (`rerun.remote_store.v1alpha1`, `rerun.log_msg.v1alpha1`, …) were renamed
to the `dalaran.*` namespace. The message definitions themselves are unchanged, but the fully
qualified service and message names are not, so:

* A Dalaran Viewer cannot talk to a Rerun gRPC server, and vice versa.
* Generated protobuf stubs are not interchangeable between the two projects.

Recorded data is unaffected by this — it is only the wire protocol that moved.

### The URI scheme

Rerun's `rerun://`, `rerun+http://` and `rerun+https://` URIs became `dalaran://`, `dalaran+http://`
and `dalaran+https://`. Rewrite the scheme when moving a URI over; the rest of the URI (origin,
dataset id, `segment_id`, `time_range`, …) has the same shape.

### SDK names

The SDKs were renamed along with everything else, so source code needs updating even though data
does not:

| | Rerun | Dalaran |
| --- | --- | --- |
| Python package | `rerun` (`import rerun as rr`) | `dalaran` (`import dalaran as dl`) |
| Python dist | `rerun-sdk` | `dalaran-sdk` |
| Rust crates | `re_*`, umbrella `rerun` | `dl_*`, umbrella `dalaran` |
| C++ namespace | `rerun::` | `dalaran::` |
| C API prefix | `rr_`/`RR_` | `dl_`/`DL_` |
| Environment variables | `RERUN_*` | `DALARAN_*` |

### Analytics and viewer state

Viewer persistence (window geometry, stored blueprints, analytics opt-out) lives in a Dalaran-specific
directory and is not shared with a Rerun installation. Blueprints saved by Rerun can still be loaded
explicitly as `.rbl` files.
