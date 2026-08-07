# dl_redap_tests

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.


![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

Official test suite for the Dalaran Data Protocol ("redap").

This test suite is specifically focused on the redap layer.
In particular it aims to cover what our API's `*.proto` files leave implicit.
This includes at least:
- all the dataframes (schema, content)
- all the stateful behaviors (e.g. chunk keys, tasks, etc.)

As such, it is implemented to be as close as possible to the actual API boundary, aka the (incorrectly named) `DalaranCloudService` trait.

## Goals

- Cover all aspects of the redap layer, including dataframe schemas and stateful behaviors.
- Serve as the definitive reference of what redap is.
- Ensure conformance of all implementations (including, possibly, third-party).

## Non-goals

- Test layers outside the redap boundary, including `dl_redap_client::ConnectionClient` or the Python SDK.
- Test anything about the internals of the redap implementors (OSS server, Dalaran Hub, etc.)

## Usage

This crate provides the test suite, but it requires an actual implementation
of the server in order to run these tests. To use the OSS dalaran server to
perform these tests use the following command

```shell
cargo test -p dl_server --all-features
```

## CI

The test suite is run against both the OSS server (`dl_server`) and the Dalaran Hub, both in-process (not against a deployed binary).

There are more e2e tests in [`e2e_redap_tests`](../../../dalaran_py/tests/e2e_redap_tests/README.md), but in Python.
