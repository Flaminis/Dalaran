# Attribution & Upstream Heritage

Dalaran is an independent, community-driven **hard fork of [Rerun](https://github.com/rerun-io/rerun)**,
created to build a robotics-first, Apache-2.0-only visualization and data
infrastructure stack.

## What we inherited

Rerun is an outstanding piece of engineering. Dalaran inherits its:

- Arrow-native chunk store and time-series data model
- `wgpu`-based renderer and `egui` viewer shell
- Multi-language SDKs (Rust, Python, C/C++)
- gRPC transport, MCAP/ROS message ingestion, and file-format tooling

Full upstream history is preserved in this repository. The fork point is
tagged as `upstream-base`, and the original upstream remote is retained:

```sh
git remote -v          # upstream -> https://github.com/rerun-io/rerun.git
git log upstream-base  # unmodified upstream history
```

## Licensing

Upstream Rerun is dual-licensed `MIT OR Apache-2.0`. Dalaran elects the
**Apache License, Version 2.0** for the entire project, so that every user gets
an explicit patent grant. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Naming

Everything user-facing has been renamed:

| Rerun                 | Dalaran                |
| --------------------- | ---------------------- |
| `rerun` (Rust crate)  | `dalaran`              |
| `re_*` crates         | `dl_*` crates          |
| `rerun-sdk` (Python)  | `dalaran-sdk`          |
| `import rerun as rr`  | `import dalaran as dl` |
| `rr_*` (C API)        | `dl_*` (C API)         |
| `rerun::` (C++)       | `dalaran::` (C++)      |
| `.rrd` files          | `.dlr` files           |
| `.rbl` blueprints     | `.dbl` blueprints      |

## Thank you

Thank you to the Rerun team and contributors. Dalaran exists *because* Rerun
chose a permissive license. We aim to be good citizens: we credit upstream
loudly, we keep history intact, and we contribute fixes back where they apply.
