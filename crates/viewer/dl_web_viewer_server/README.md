# dl_web_viewer_server

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_web_viewer_server.svg)](https://crates.io/crates/dl_web_viewer_server)
[![Documentation](https://docs.rs/dl_web_viewer_server/badge.svg)](https://docs.rs/dl_web_viewer_server)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

Serves the Dalaran web viewer (`dl_viewer` as Wasm and HTML) over HTTP.

When developing, you must run `pixi run dalaran-build-web` (or `pixi run dalaran-build-web-release`), before building this package.
This is done automatically with `pixi run dalaran-web`.

## Embedding modes

By default, web viewer assets are embedded at compile time using `include_bytes!`.

When built with `DALARAN_TRAILING_WEB_VIEWER=1`, the assets are expected to be appended to the binary via a post-processing step using `scripts/append_web_viewer.py`. This allows parallel building of CLI and web viewer in CI. Binaries built this way will fail to create a `WebViewerServer` before the post-processing step completes.

When built with `DALARAN_EXTERNAL_WEB_VIEWER=1`, there are no built-in assets at all: they must be loaded at runtime from a zip archive on disk. This is used by Python wheels that ship the assets as `dalaran_sdk/web_viewer.zip` instead of embedding them in the extension module.

Independently of how the binary was built, the assets can also be loaded at runtime from a zip archive on disk, via `WebViewerServer::with_archive`.
