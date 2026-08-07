---
title: Roadmap
order: 0
---

The authoritative roadmap lives in [`ROADMAP.md`](https://github.com/Flaminis/Dalaran/blob/main/ROADMAP.md) in the repository, so that it is versioned alongside the code it describes and can be updated in the same pull request as the work.

In short, Dalaran is building an Apache-2.0, robotics-first observability and visualization stack for multimodal time-series data, and everything it ships runs on your own hardware.

Near-term work is concentrated on the robotics surface: a high-level `dalaran.robot` logging API, ROS axis-convention helpers, occupancy grids and costmaps, a `dalaran doctor` diagnostic command, and reading existing `.rrd` recordings directly. Mid-term work is the ROS 2 bridge with an extensible message registry, rosbag2 replay, `.dlrpack` dataset bundles, web viewer parity, and documented cloud-free self-hosting.

Alongside those, we continually work on performance, developer experience, and support for more data types.

We are explicitly *not* building a hosted commercial service, and we do not hold features back to make one viable.

The roadmap is subject to change, and GitHub is the most authoritative source for what is actually in progress:

- [Issue tracker](https://github.com/Flaminis/Dalaran/issues) — open an issue, or 👍 an existing one to tell us it matters to you
- [Discussions](https://github.com/Flaminis/Dalaran/discussions) — for design conversations that are not yet a concrete issue
- [`CONTRIBUTING.md`](https://github.com/Flaminis/Dalaran/blob/main/CONTRIBUTING.md) — how to propose a feature so that it gets a useful response
