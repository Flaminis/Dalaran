# The Dalaran Viewer

Part of the [`dalaran`](https://github.com/rerun-io/rerun) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_viewer.svg)](https://crates.io/crates/viewer/dl_viewer)
[![Documentation](https://docs.rs/dl_viewer/badge.svg)](https://docs.rs/dl_viewer)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

This is the main crate with all the GUI.

This can be compiled as a web-app by building for Wasm. To run it natively, use the `dalaran` binary.

Talks to the server over gRPC (using `dl_redap_client`).
