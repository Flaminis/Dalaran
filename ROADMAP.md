# Dalaran roadmap

This is what we intend to build, in rough order. It is not a schedule and it is
not a promise: dates are deliberately absent, and items move between sections
as we learn things. If something here matters to you, say so on the
[issue tracker](https://github.com/Flaminis/Dalaran/issues) — that is the main
signal we use to reorder this list.

Nothing in this document is shipped unless it also appears as working code in
the repository. See the [README](README.md) for what actually works today.

## Near term

The things we are working on now, or next.

- **`dalaran.robot` high-level API.** A single handle that understands a robot:
  joint states, base pose, sensor frames, URDF-driven link transforms. The goal
  is that logging a robot correctly takes five lines and does not require the
  user to get quaternion order and frame parentage right by hand.
- **ROS axis-convention helpers.** REP-103/REP-105 conventions as first-class
  helpers — `x`-forward `z`-up, ENU vs. NED, and the `map`/`odom`/`base_link`
  frame semantics — because a silently mismatched convention produces a
  visualization that is confidently wrong.
- **Occupancy grids and costmaps.** `nav_msgs/OccupancyGrid` and layered
  costmaps as a real archetype with origin, resolution, and unknown-cell
  handling, rather than being flattened into an untyped image.
- **`dalaran doctor`.** A diagnostic subcommand covering GPU and driver
  detection, viewer/SDK version skew, ROS 2 environment sanity, and recording
  integrity, reporting in plain language with a suggested fix per finding.
- **Reading existing `.rrd` recordings.** The container format is unchanged
  from upstream — same `RRF2` fourcc — so this is mostly extension and
  content-type plumbing plus a migration path for older schema generations.
  Renaming an `.rrd` to `.dlr` already works; `dalaran recording.rrd` should
  work too.
- **Documentation that matches the product.** A few pages still describe
  behaviour we have since changed. This is unglamorous and we are doing it
  anyway, because docs that lie are worse than missing docs.

## Mid term

Larger pieces that depend on the near-term work landing first.

- **ROS 2 bridge with an extensible message registry.** Subscribe to live
  topics and replay rosbag2 files, with a registry that lets you register your
  own `.msg` definitions at runtime instead of patching and rebuilding the
  core. Parity target is the message set that a typical Nav2 + perception stack
  actually publishes, not an exhaustive list.
- **rosbag2 replay ergonomics.** Seeking, rate control, topic filtering, and
  partial ingestion of very large bags without loading everything into memory.
- **`.dlrpack` portable dataset bundles.** One file carrying recordings, the
  blueprint, referenced assets (meshes, URDFs, calibration), and metadata, so
  sharing a failing run is a single artifact rather than a folder and a set of
  instructions.
- **Dataset-level tooling.** Registering many recordings, querying across them,
  and slicing out training sets, using the catalog server that is already in
  this tree.
- **Web viewer parity.** The web build should be a first-class way to review a
  recording — including large point clouds and video — not a degraded preview.
- **Cloud-free self-hosting.** A documented, supported way to run the catalog
  and viewer entirely on your own hardware, including an air-gapped setup, with
  no telemetry and no external service dependency.

## Long term

Direction rather than plan. These are the problems we think are worth solving;
we have not committed to an approach for any of them.

- **Full ROS 2 parity as an ingestion target**, including QoS-aware live
  subscription, lifecycle-node awareness, and round-tripping back out to a bag.
- **Multi-robot and fleet-scale review**: many recordings from many machines on
  one timeline, with the query layer doing the heavy lifting.
- **Deeper time-series analysis in the viewer** — comparing two runs, diffing
  trajectories, and annotating what went wrong — so that review does not always
  have to move to a notebook.
- **Hardware-in-the-loop and simulator integrations** beyond generic logging.
- **Long-term format stability**, with a documented compatibility guarantee, so
  a recording taken today is still readable in several years.

## Explicitly not planned

Saying no is part of a roadmap.

- **A hosted commercial service.** Dalaran is Apache-2.0 software you run
  yourself. We are not building a SaaS product, and no feature will be held
  back to make one viable.
- **Telemetry that phones home by default.**
- **Non-permissive or copyleft dependencies** in the core. Apache-2.0
  compatibility is a hard constraint on what we can take on.
- **Becoming a general-purpose plotting library.** If your data is not
  multimodal and not time-indexed, there are better tools.
