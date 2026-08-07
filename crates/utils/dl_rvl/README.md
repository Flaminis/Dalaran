# dl_rvl

Part of the [`dalaran`](https://github.com/rerun-io/rerun) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_rvl.svg)](https://crates.io/crates/dl_rvl)
[![Documentation](https://docs.rs/dl_rvl/badge.svg)](https://docs.rs/dl_rvl)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

Codecs and helpers for depth compression formats, with a focus on RVL (Run length encoding and Variable Length encoding schemes).
Includes utilities to parse `compressedDepth` metadata as well as decode RVL streams into either disparity (`u16`) or metric depth (`f32`) buffers.
