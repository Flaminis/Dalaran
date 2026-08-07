# Dalaran server

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_server.svg)](https://crates.io/crates/dl_server)
[![Documentation](https://docs.rs/dl_server/badge.svg)](https://docs.rs/dl_server)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

In-memory opensource implementation of the Dalaran server.

The goal for this crate is to support most of the same gRPC endpoints that our commercial Dalaran Hub service supports, but do so in-memory for maximum simplicity.

We use this internally for testing, but in the future it might be useful for users too.

This is (currently) NOT the server you get when running `dalaran --serve-grpc`, though we hope to unify the two at some point.
