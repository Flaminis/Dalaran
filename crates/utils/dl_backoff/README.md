# dl_backoff

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_backoff.svg)](https://crates.io/crates/dl_backoff)
[![Documentation](https://docs.rs/dl_backoff/badge.svg)](https://docs.rs/dl_backoff)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

Implements utility code to help with backoff and retry logic.

### Why not use existing traits like backoff, backon, tokio-retry2, or tower(retry)?

The code is small and simple, that it feels unnecessary to add an external dependency for it. We should re-evaluate should this become ever-complicated.
