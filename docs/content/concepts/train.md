---
title: Train
order: 400
description: Feed catalog recordings into training pipelines via export or PyTorch
---

A Dalaran [catalog](query-and-transform/catalog-object-model.md) can feed training pipelines two ways: export recordings to a standard format, or stream them directly into a PyTorch `DataLoader`.

## Export to a training format

The catalog exposes recordings as queryable DataFrames via [DataFusion](https://datafusion.apache.org/python/).
Multi-rate sensor streams can be time-aligned and columns of interest extracted, with the result written to whatever format a training pipeline expects.

See [Export recordings to LeRobot datasets](../howto/train/lerobot_export.md) for a worked example.

## Train directly from the catalog

The experimental [`dalaran.experimental.dataloader`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/) module wraps a catalog as iterable or map-style PyTorch datasets, with no intermediate export step.

### Sample space

Three things describe a dataset (see [reference](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/)):

- **[`DataSource`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/#dalaran.experimental.dataloader.DataSource)** — a catalog `DatasetEntry` with an optional segment filter; each registered DLR is one *segment*, typically one episode or trajectory
- **`index`** — the timeline that defines what "one sample" means (e.g. `"frame_index"` or `"real_time"`)
- **`fields`** — a dict of [`Field`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/#dalaran.experimental.dataloader.Field)s, each mapping a source column (an `entity:Archetype:component` triple) to a decoder

[`SampleIndex`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/#dalaran.experimental.dataloader.SampleIndex) pre-computes the full sample space from lightweight per-segment index-range metadata — one query per segment, not a scan of the data.
For timestamp timelines, `FixedRateSampling` defines the sampling grid and the server handles drift between grid and real row positions via `fill_latest_at`.

### Decoders

Each `Field` has a `ColumnDecoder` ([`_decoders.py`](https://github.com/Flaminis/Dalaran/blob/main/rerun_py/rerun_sdk/rerun/experimental/dataloader/_decoders.py)) that converts a raw Arrow column to a `torch.Tensor`:

- [`NumericDecoder`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/#dalaran.experimental.dataloader.NumericDecoder) — scalars and numeric lists
- [`ImageDecoder`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/#dalaran.experimental.dataloader.ImageDecoder) — JPEG/PNG blobs
- [`VideoFrameDecoder`](https://ref.dalaran.dev/docs/python/stable/experimental_dataloader/#dalaran.experimental.dataloader.VideoFrameDecoder) — compressed video (`h264`/`h265`/`av1`)

### Windows

`Field(window=(start, end))` returns a slice of values across an inclusive range relative to the current sample rather than a single value.
This is how action chunks and observation history are expressed.

### Dataset styles

- `DalaranIterableDataset` — streaming with automatic shuffling and cross-worker and DDP partitioning
- `DalaranMapDataset` — random access by global index; works with PyTorch samplers like `DistributedSampler` and `WeightedRandomSampler`

See [Train PyTorch models with Dalaran](../howto/train/dataloader.md) for usage.
