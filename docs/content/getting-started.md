---
title: Getting Started
order: 1
---

Dalaran helps robotics and Physical AI teams iterate faster: log from any sensor, visualize in the Viewer, query with dataframes, and train with a dataloader tailored to robotic learning — across one recording or many.

## Installation

`pip install dalaran-sdk[dataplatform, dataloader]` bundles the **SDK** (log/query from code) and the **Viewer** (visualizer app). The optional dependencies support queries and training below.
For Rust, C++, see [Install Dalaran](./getting-started/install-dalaran.md) and [Set up a project](./getting-started/project-setup.md).

## Open the Viewer

`dalaran` launches the Viewer.
Pass a file to open it directly:

```bash
dalaran path/to/recording.rrd
```

Supports `.rrd`, `.mcap`, and [more](./getting-started/data-in/open-any-file.md).
Also available in-browser at [dalaran.dev/viewer](https://dalaran.dev/viewer).


## Scale across many recordings

Dalaran's catalog organizes recordings as queryable [**segments**](./concepts/query-and-transform/catalog-object-model.md).
The workflow: log (or convert) data to an `.rrd`, start a catalog server (or connect to an existing one if using the commercial Dalaran Hub), register the `.rrd` as a segment, then visualize and query across recordings.

### Log

Save data to an `.rrd` see [Log and Ingest](./getting-started/data-in.md) for more details.
If you already have data in another format see our [how-to](https://dalaran.dev/docs/howto/logging-and-ingestion) for various examples converting to `.rrd`.

snippet: tutorials/getting_started_log
### Start a catalog server

`dalaran server` starts a local catalog on port `51234` (use Dalaran Hub for persistent, multi-user storage), then connect from your code:

```bash
dalaran server
```

snippet: tutorials/getting_started[setup]

### Ingest

Register an `.rrd` with a dataset so it shows up as a queryable segment.

snippet: tutorials/getting_started[ingest]

### Visualize

Point the Viewer at your server to browse every recording in the catalog.
See [Configure the Viewer](./getting-started/configure-the-viewer.md).

```bash
dalaran dalaran+http://127.0.0.1:51234
```

### Query

Query the catalog into a [DataFusion](https://datafusion.apache.org/) DataFrame. See [Query and Transform](./getting-started/data-out.md).

snippet: tutorials/getting_started[query]

### Train

Connect a Dataloader to the server to generate training batches. See [Train](./getting-started/train.md).

snippet: tutorials/getting_started[train]

## If you're stuck

-   Check the [troubleshooting guide](./getting-started/install-dalaran/troubleshooting.md).
-   [Open an issue](https://github.com/rerun-io/rerun/issues/new/choose).
-   [Join the Discord server](https://discord.gg/PXtCgFBSmH).
