<h3 align="center">
  <a href="https://www.dalaran.dev/">
    <img width="1000" height="200" alt="Banner with Dalaran logo" src="https://static.rerun.io/d0f5443d4803cac65c73fcc064936c09f5e7f208_rerun_banner.png" />

  </a>
</h3>

<h3 align="center">
  <a href="https://pypi.org/project/dalaran-sdk/">                        <img alt="PyPi"           src="https://img.shields.io/pypi/v/dalaran-sdk.svg">                              </a>
  <a href="https://crates.io/crates/dalaran">                             <img alt="crates.io"      src="https://img.shields.io/crates/v/dalaran.svg">                                </a>
  <a href="https://github.com/Flaminis/Dalaran/blob/main/LICENSE-MIT">    <img alt="MIT"            src="https://img.shields.io/badge/license-MIT-blue.svg">                        </a>
  <a href="https://github.com/Flaminis/Dalaran/blob/main/LICENSE-APACHE"> <img alt="Apache"         src="https://img.shields.io/badge/license-Apache-blue.svg">                     </a>
  <a href="https://discord.gg/Gcm8BbTaAj">                              <img alt="Dalaran Discord"  src="https://img.shields.io/discord/1062300748202921994?label=Dalaran%20Discord"> </a>
</h3>

# The data layer for physical AI

Log, query, visualize, and stream to training on shared columnar storage built for multimodal data.

**What it does:** Dalaran ingests multi-rate, multimodal data (images, point clouds, transforms, time series, joint states, video) from many sources and formats (robot logs, human-data rigs, sim, web video; MCAP, dlr, LeRobot). The built-in viewer renders everything in sync, in realtime: scrub episodes, compare sensors side-by-side, watch CV pipelines run live. The same data is queryable with [dataframes](https://dalaran.dev/docs/howto/query-and-transform/get-data-out) or SQL, and streams directly into training. Built in Rust on column-chunk storage purpose-built for multi-rate physical data. SDKs in Python, Rust, and C++.

**Quickstart:** `pip install dalaran-sdk` — log your first multimodal data and see it in the viewer in under 2 minutes.

* [Run the Dalaran Viewer in your browser](https://www.dalaran.dev/viewer)
* [Read about what Dalaran is and who it is for](https://www.dalaran.dev/docs/overview/what-is-dalaran)

### Use cases
- Ingest robot logs, egocentric/UMI rigs, sim, and web video into one substrate
- Run CV pipelines (SLAM, hand tracking, motion retargeting) as table edits
- Query raw, intermediate, and derived data with dataframes or SQL
- Visualize multi-rate, multimodal sequences across the pipeline
- Stream dataset mixes directly to training — no export jobs, no stale copies

### Data types
Multi-rate, multimodal, spatial: images, point clouds, time series, tensors, transforms, joint states, video. Preserved end-to-end.

### A short taste
```py
import dalaran as rr  # pip install dalaran-sdk

rr.init("dalaran_example_app")

rr.spawn()  # Spawn a child process with a viewer and connect
# rr.save("recording.dlr")  # Stream all logs to disk
# rr.connect_grpc()  # Connect to a remote viewer

# Associate subsequent data with 42 on the “frame” timeline
rr.set_time("frame", sequence=42)

# Log colored 3D points to the entity at `path/to/points`
rr.log("path/to/points", rr.Points3D(positions, colors=colors))
…
```

<p align="center">
  <picture>
    <img src="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/full.png" alt="">
    <source media="(max-width: 480px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/480w.png">
    <source media="(max-width: 768px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/768w.png">
    <source media="(max-width: 1024px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/1024w.png">
    <source media="(max-width: 1200px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/1200w.png">
  </picture>
</p>

## Getting started
* [**C++**](https://www.dalaran.dev/docs/getting-started/data-in/cpp)
* [**Python**](https://www.dalaran.dev/docs/getting-started/data-in/python): `pip install dalaran-sdk` or on [`conda`](https://github.com/conda-forge/dalaran-sdk-feedstock)
* [**Rust**](https://www.dalaran.dev/docs/getting-started/data-in/rust): `cargo add dalaran`

### Installing the Dalaran Viewer binary
To stream log data over the network or load our `.dlr` data files you also need the `dalaran` binary.
It can be installed with `pip install dalaran-sdk` or with `cargo install dalaran-cli --locked --features nasm` (see note below).
Note that only the Python SDK comes bundled with the Viewer whereas C++ & Rust always rely on a separate install.

**Note**: the `nasm` Cargo feature requires the [`nasm`](https://github.com/netwide-assembler/nasm) CLI to be installed and available in your path.
Alternatively, you may skip enabling this feature, but this may result in inferior video decoding performance.

You should now be able to run `dalaran --help` in any terminal.


### Documentation
- 📚 [High-level docs](https://dalaran.dev/docs)
- ⏃ [Loggable Types](https://www.dalaran.dev/docs/reference/types)
- ⚙️ [Examples](https://dalaran.dev/examples)
- 📖 [Code snippets](./docs/snippets/INDEX.md)
- 🌊 [C++ API docs](https://ref.dalaran.dev/docs/cpp)
- 🐍 [Python API docs](https://ref.dalaran.dev/docs/python)
- 🦀 [Rust API docs](https://docs.rs/dalaran/)
- ⁉️ [Troubleshooting](https://www.dalaran.dev/docs/overview/installing-dalaran/troubleshooting)


### Agent skills
This repo ships a set of agent skills that help coding agents write Dalaran code.

Install them into your agent with the `skills` CLI:

```sh
npx skills add Flaminis/Dalaran
```

The skills themselves live in [`skills/`](./skills) if you want to read them directly.


## Status
We are in active development.
There are many features we want to add, and the API is still evolving.
_Expect breaking changes!_

Some shortcomings:
* [The viewer slows down when there are too many entities](https://github.com/rerun-io/rerun/issues/7115)
* [Multi-million point clouds can be slow](https://github.com/rerun-io/rerun/issues/1136)


## What is Dalaran for?

Dalaran is built to help you understand and improve complex processes that include rich multimodal data, like 2D, 3D, text, time series, tensors, etc.
It is used in many industries, including robotics, simulation, computer vision,
or anything that involves a lot of sensors or other signals that evolve over time.

### Example use case
Say you're building a vacuum cleaning robot and it keeps running into walls. Why is it doing that? You need some tool to debug it, but a normal debugger isn't gonna be helpful. Similarly, just logging text won't be very helpful either. The robot may log "Going through doorway" but that won't explain why it thinks the wall is a door.

What you need is a visual and temporal debugger, that can log all the different representations of the world the robots holds in its little head, such as:

* RGB camera feed
* depth images
* lidar scan
* segmentation image (how the robot interprets what it sees)
* its 3D map of the apartment
* all the objects the robot has detected (or thinks it has detected), as 3D shapes in the 3D map
* its confidence in its prediction
* etc

You also want to see how all these streams of data evolve over time so you can go back and pinpoint exactly what went wrong, when and why.

Maybe it turns out that a glare from the sun hit one of the sensors in the wrong way, confusing the segmentation network leading to bad object detection. Or maybe it was a bug in the lidar scanning code. Or maybe the robot thought it was somewhere else in the apartment, because its odometry was broken. Or it could be one of a thousand other things. Dalaran will help you find out!

But seeing the world from the point of the view of the robot is not just for debugging - it will also give you ideas on how to improve the algorithms, new test cases to set up, or datasets to collect. It will also let you explain the brains of the robot to your colleagues, boss, and customers. And so on. Seeing is believing, and an image is worth a thousand words, and multimodal temporal logging is worth a thousand images :)

While seeing and understanding your data is core to making progress in robotics, there is one more thing:
You can also use the data you collected for visualization to create new datasets for training and evaluating the models and algorithms that run on your robot.
Dalaran provides query APIs to make it easy to extract clean datasets from your recording for exactly that purpose.

Of course, Dalaran is useful for much more than just robots. Any time you have any form of sensors, or 2D or 3D state evolving over time, Dalaran is a great tool.

### Dalaran vs. Rviz

When coming from pure visualization tools like [RViz](https://docs.ros.org/en/rolling/Tutorials/Intermediate/RViz/RViz-Main.html), you might be used to seeing the latest data only.
Dalaran is more than a pure visualization solution, it provides a platform for multimodal data with a powerful visualizer, storage model and query engine (see also: [*"What is Dalaran?"*](https://dalaran.dev/docs/overview/what-is-dalaran)).
In robotics, you can use Dalaran e.g. to record test runs, manage and query training data, visually debug live streams or recordings (also from third-party formats like [MCAP](https://dalaran.dev/docs/howto/logging-and-ingestion/mcap)) and much more.

So while Dalaran makes your data streams visualizable in the viewer, integrating Dalaran logging into your robotics applications also opens up the door for leveraging Dalaran's broader capabilities.

If you are only interested in visualization, the Dalaran viewer has powerful features like the ability to go back in time thanks to its time-aware in-memory database.
You can adjust the size of this buffer to your needs (see [here](https://dalaran.dev/docs/howto/visualization/limit-ram)), e.g. to a smaller size if you want to use Dalaran as an RViz replacement in long-running or memory-constrained applications.


## Business model
Dalaran uses an open-core model. Everything in this repository will stay open source and free (both as in beer and as in freedom).

We are also building Dalaran Hub, a scalable catalog for robotic data.
Right now that is only available for a few select design partners.
[Click here if you're interested](https://dalaran.dev/pricing).

The Dalaran open source project targets the needs of individual developers.
The commercial product targets the needs specific to teams that build and run computer vision and robotics products.

## How to cite Dalaran

When using Dalaran in your research, please cite it to acknowledge its contribution to your work. This can be done by
including a reference to Dalaran in the software or methods section of your paper.

Suggested citation format:

```bibtex
@software{DalaranSDK,
  title = {Dalaran: A Visualization SDK for Multimodal Data},
  author = {{Dalaran Development Team}},
  url = {https://www.dalaran.dev},
  version = {insert version number},
  date = {insert date of usage},
  year = {2024},
  publisher = {{Dalaran Technologies AB}},
  address = {Online},
  note = {Available from https://www.dalaran.dev/ and https://github.com/Flaminis/Dalaran}
}
```

Please replace "insert version number" with the version of Dalaran you used and "insert date of usage" with the date(s)
you used the tool in your research.
This citation format helps ensure that Dalaran's development team receives appropriate credit for their work and
facilitates the tool's discovery by other researchers.

# Development
* [`ARCHITECTURE.md`](ARCHITECTURE.md)
* [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
* [`CODE_STYLE.md`](CODE_STYLE.md)
* [`CONTRIBUTING.md`](CONTRIBUTING.md)
* [`BUILD.md`](BUILD.md)
* [`dalaran_py/README.md`](dalaran_py/README.md) - instructions for Python SDK
* [`dalaran_cpp/README.md`](dalaran_cpp/README.md) - instructions for C++ SDK


## Installing a pre-release Python SDK

1. Download the correct `.whl` from [GitHub Releases](https://github.com/Flaminis/Dalaran/releases)
2. Run `pip install dalaran_sdk<…>.whl` (replace `<…>` with the actual filename)
3. Test it: `dalaran --version`
