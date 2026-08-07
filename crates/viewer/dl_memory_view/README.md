# dl_memory_view

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_memory_view.svg)](https://crates.io/crates/dl_memory_view)
[![Documentation](https://docs.rs/dl_memory_view/badge.svg)](https://docs.rs/dl_memory_view)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

Flamegraph visualization for memory usage trees.

This crate provides an interactive flamegraph widget for visualizing `MemUsageTree` structures from dl_byte_size.

## Running the demo

To see the flamegraph in action, run the demo application:

```bash
cargo run --example demo -p dl_memory_view
```

The demo creates a sample memory hierarchy showing various subsystems (viewer, store, cache, etc.)
and allows you to interact with the flamegraph visualization.
