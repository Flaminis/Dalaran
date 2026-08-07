<p align="center">
  <img width="360" alt="Dalaran" src="docs/assets/dalaran-wordmark.svg" />
</p>

<p align="center">
  <a href="https://pypi.org/project/dalaran-sdk/"><img alt="PyPI" src="https://img.shields.io/pypi/v/dalaran-sdk.svg"></a>
  <a href="https://crates.io/crates/dalaran"><img alt="crates.io" src="https://img.shields.io/crates/v/dalaran.svg"></a>
  <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg"></a>
</p>

# Dalaran

**Dalaran is an Apache-2.0, robotics-first observability and visualization stack
for multimodal time-series data — ROS 2 topics, LiDAR sweeps, camera streams,
IMU, and TF transforms, recorded and replayed on one timeline.**

You log data from your robot, your simulator, or an offline pipeline; Dalaran
stores it in an Arrow-backed columnar chunk store, renders it in a 3D/2D viewer
that stays in sync across every sensor, and hands the same data back to you as
dataframes when you want to compute on it instead of look at it.

---

## Dalaran is a hard fork of Rerun

Dalaran began as a hard fork of [Rerun](https://github.com/rerun-io/rerun), and
we want to be explicit about that rather than quietly rename a codebase and
pretend otherwise. Rerun's Arrow-native chunk store, its `wgpu` renderer and
`egui` viewer shell, its Rust/Python/C++ SDKs, and its file-format tooling are
excellent engineering, and Dalaran inherits all of it. The fork exists to take
the project in a specific direction — robotics-first APIs, a single permissive
licence, and a stack you can run entirely on your own hardware — not because
anything was wrong upstream.

Upstream is dual-licensed `MIT OR Apache-2.0`; Dalaran elects **Apache-2.0**
for the whole project so every user gets an explicit patent grant. Full upstream
history is preserved in this repository, the fork point is tagged
`upstream-base`, and we send fixes back upstream when they apply there.

See [ATTRIBUTION.md](ATTRIBUTION.md) for the complete heritage, the licensing
rationale, and the old-name/new-name mapping.

---

## 60-second quickstart

### Python

```sh
pip install dalaran-sdk
```

```python
import dalaran as dl
import numpy as np

dl.init("dalaran_example_app", spawn=True)  # spawn a viewer process and stream to it

positions = np.random.default_rng(0).normal(size=(1000, 3)).astype(np.float32)
colors = np.random.default_rng(1).integers(0, 255, size=(1000, 3), dtype=np.uint8)

for frame in range(100):
    dl.set_time("frame", sequence=frame)
    dl.log("world/points", dl.Points3D(positions + frame * 0.01, colors=colors))
```

Write to a file instead of a live viewer with `dl.save("session.dlr")`, then
open it later with `dalaran session.dlr`.

### Rust

```sh
cargo add dalaran
```

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_app").spawn()?;

    let positions: Vec<_> = (0..1000)
        .map(|i| ((i % 10) as f32, ((i / 10) % 10) as f32, (i / 100) as f32))
        .collect();

    rec.set_time_sequence("frame", 0);
    rec.log("world/points", &dalaran::Points3D::new(positions))?;

    Ok(())
}
```

### C++

Fetch the SDK in your `CMakeLists.txt` and link against `dalaran_sdk`:

```cmake
include(FetchContent)
FetchContent_Declare(dalaran_sdk URL
  https://github.com/Flaminis/Dalaran/releases/latest/download/dalaran_cpp_sdk.zip)
FetchContent_MakeAvailable(dalaran_sdk)
target_link_libraries(your_target PRIVATE dalaran_sdk)
```

```cpp
#include <dalaran.hpp>

int main() {
    const auto rec = dalaran::RecordingStream("dalaran_example_app");
    rec.spawn().exit_on_failure();

    rec.set_time_sequence("frame", 0);
    rec.log("world/points", dalaran::Points3D({{0.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}}));
}
```

### The viewer and CLI

The `dalaran` binary is both the viewer and the CLI. It ships with the Python
wheel, or you can install it on its own:

```sh
cargo install dalaran-cli --locked
dalaran --help
dalaran session.dlr        # open a recording
dalaran --serve            # serve a web viewer
```

Recordings are `.dlr` files and saved blueprints are `.dbl` files. Live streams
and remote catalogs are addressed with `dalaran://` URIs.

---

## Why Dalaran

Everything below is what this fork is adding on top of what it inherited. Items
marked *(in progress)* are being actively built and are not something you should
depend on yet; unmarked items work today.

- **`dalaran.robot`, a high-level robotics logging API** *(in progress)* — one
  handle that knows about a robot: joint states, base pose, sensor frames, and
  URDF-driven link transforms, so you log `robot.joint_states(...)` instead of
  hand-rolling a dozen entity paths and quaternion conversions.
- **ROS 2 bridge and rosbag2 replay** *(in progress)* — subscribe to live ROS 2
  topics or replay a rosbag2 into Dalaran, backed by an **extensible message
  registry** so you can teach it your own `.msg` types without patching the
  core. Today the repository already ingests MCAP and a set of common ROS
  message schemas.
- **ROS axis-convention helpers** *(in progress)* — REP-103/REP-105 conventions
  (`x`-forward `z`-up, ENU vs. NED, `map`/`odom`/`base_link` frame semantics)
  as first-class helpers, because silently mismatched axis conventions are the
  single most common way a robotics visualization ends up wrong.
- **Occupancy grids and costmaps** *(in progress)* — `nav_msgs/OccupancyGrid`
  and layered costmaps as a real archetype with proper origin/resolution
  handling, instead of being flattened into an untyped image.
- **`dalaran doctor`** *(in progress)* — a diagnostic subcommand that inspects
  your environment (GPU and driver, viewer/SDK version skew, ROS 2 setup,
  recording integrity) and tells you what is wrong in plain language.
- **`.dlrpack` portable dataset bundles** *(in progress)* — a single file that
  carries recordings, the blueprint, referenced assets, and metadata, so
  "here is the run that failed" is one artifact you can hand to a colleague.
- **Apache-2.0 throughout, self-hostable** — no dual-licence ambiguity, no
  hosted-service dependency. Everything in this repository runs on your own
  machines, and the catalog server is part of the open-source tree.

## Reading existing `.rrd` recordings

Dalaran did not fork the storage format. The on-disk container still uses the
`RRF2` fourcc, so a `.dlr` file and an upstream `.rrd` file of the same
generation are the same bytes with a different extension, and you can rename an
`.rrd` to `.dlr` to open it. Native `.rrd` extension handling — so that
`dalaran recording.rrd` just works without renaming — is *in progress*. Deep
schema compatibility across major versions is bounded by the same migration
rules that apply upstream: recordings from very old versions may need a
migration pass.

## Architecture

Rust crates live under `crates/` and are prefixed `dl_*`. The table lists the
ones worth knowing about first; each directory has its own `README.md`.

| Crate | Group | What it does |
| --- | --- | --- |
| [`dalaran`](crates/top/dalaran) | top | Umbrella crate. What `cargo add dalaran` gives you. |
| [`dalaran-cli`](crates/top/dalaran-cli) | top | The `dalaran` binary: viewer, CLI, web server. |
| [`dl_sdk`](crates/top/dl_sdk) | top | The logging SDK proper: `RecordingStream` and sinks. |
| [`dalaran_c`](crates/top/dalaran_c) | top | C API (`dl_`/`DL_` prefixed), which the C++ SDK wraps. |
| [`dl_types`](crates/store/dl_types) | store | Generated archetypes, components, and datatypes. |
| [`dl_log_types`](crates/store/dl_log_types) | store | Entity paths, timelines, and core log primitives. |
| [`dl_chunk`](crates/store/dl_chunk) | store | The Arrow chunk: the unit of data everything moves in. |
| [`dl_chunk_store`](crates/store/dl_chunk_store) | store | Indexed storage and retrieval of chunks. |
| [`dl_query`](crates/store/dl_query) | store | Latest-at and range queries over the store. |
| [`dl_dataframe`](crates/store/dl_dataframe) | store | Dataframe view of a recording, for getting data back out. |
| [`dl_log_encoding`](crates/store/dl_log_encoding) | store | The `.dlr` container: encode, decode, migrate. |
| [`dl_mcap`](crates/store/dl_mcap) | store | MCAP ingestion. |
| [`dl_ros_msg`](crates/utils/dl_ros_msg) | utils | ROS message schema parsing and decoding. |
| [`dl_tf`](crates/store/dl_tf) | store | Transform trees and frame resolution. |
| [`dl_server`](crates/store/dl_server) | store | Self-hostable catalog/data server. |
| [`dl_viewer`](crates/viewer/dl_viewer) | viewer | The viewer application shell. |
| [`dl_renderer`](crates/viewer/dl_renderer) | viewer | `wgpu` rendering backend. |

Language bindings live in [`dalaran_py/`](dalaran_py) (Python, package
`dalaran`, distribution `dalaran-sdk`), [`dalaran_cpp/`](dalaran_cpp) (C++,
namespace `dalaran::` with the alias `dl`), and [`dalaran_js/`](dalaran_js)
(web).

[`ARCHITECTURE.md`](ARCHITECTURE.md) has the long version.

## Documentation

- [User docs](docs/content) — concepts, how-to guides, and reference
- [Code snippets index](docs/snippets/INDEX.md)
- [Examples](examples)
- [`BUILD.md`](BUILD.md) — building from source
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — how the pieces fit together
- [`ROADMAP.md`](ROADMAP.md) — what we are doing next, and what we are not

## Status

Dalaran is under active development and the API is still evolving. Expect
breaking changes between releases, and read [`CHANGELOG.md`](CHANGELOG.md)
before upgrading. We would rather ship a small honest surface than a large
speculative one, so features listed as *in progress* above are exactly that.

## Contributing

Bug reports, robotics-integration reports, and pull requests are welcome. Start
with [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev setup, commit
conventions, and sign-off requirement, and please read
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

Security issues should not go through the public issue tracker — see
[`SECURITY.md`](SECURITY.md).

## Branding

The Dalaran mark and wordmark live in [`docs/assets/`](docs/assets) and are
original artwork. [`docs/assets/BRANDING.md`](docs/assets/BRANDING.md) describes
the palette and how you may use them.

## License

Apache License, Version 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
