# Releases and versioning

This document describes how Dalaran is versioned and released. It will change as
the project matures.

## See also

-   [`ARCHITECTURE.md`](ARCHITECTURE.md)
-   [`BUILD.md`](BUILD.md)
-   [`CONTRIBUTING.md`](CONTRIBUTING.md)
-   [`CODE_STYLE.md`](CODE_STYLE.md)
-   [`CHANGELOG.md`](CHANGELOG.md)

## Versioning

Dalaran uses semantic versioning, starting at `0.1.0`. While the major version
is `0`, a minor bump (`0.1.0` → `0.2.0`) may contain breaking changes and a
patch bump (`0.1.1`) may not.

Every artifact is versioned in lockstep from a single source of truth, the
`[workspace.package] version` in the root `Cargo.toml`:

-   all `dl_*` Rust crates, plus `dalaran`, `dalaran-cli` and `dalaran_c`
-   the Python SDK (`dalaran-sdk`) and the notebook widget
-   the C/C++ SDK, including `DALARAN_SDK_HEADER_VERSION` in
    `dalaran_cpp/src/dalaran/c/sdk_info.h`
-   the npm packages under `dalaran_js/`

A version bump therefore touches all of them. Grep for the old version string
before committing to be sure nothing was missed:

```sh
grep -rn "<old-version>" --include='*.toml' --include='*.json' --include='*.h' .
```

## Release cadence

There is no fixed cadence. Releases happen when there is something worth
shipping. Incomplete work belongs behind a feature flag rather than blocking a
release.

## Cutting a release

There is no release automation in this repository (see
[`.github/workflows/README.md`](.github/workflows/README.md)), so a release is a
deliberate, manual, verifiable sequence:

1.  Update the version everywhere, as described above.
2.  Write the [`CHANGELOG.md`](CHANGELOG.md) entry. Describe what changed for
    users, not which files moved.
3.  Verify locally, and do not skip this:

    ```sh
    export PROTOC=$(which protoc)
    pixi run ensure-pyo3-build-cfg
    cargo check --workspace --all-features   # 0 errors, 0 warnings
    cargo fmt --all --check
    ruff check . && ruff format --check .
    python3 -m pytest dalaran_py/tests/unit -q
    ```

4.  Tag the commit: `git tag -a 0.1.0 -m "Dalaran 0.1.0" && git push origin 0.1.0`
5.  Publish, if and when the registries are set up. Always dry-run first:

    ```sh
    cargo publish --dry-run -p dalaran
    pixi run py-build --release      # produces the wheel
    ```

## Compatibility

Recordings written by any `0.x` release are readable by later `0.x` releases
unless the changelog says otherwise. Dalaran also reads recordings produced by
upstream Rerun; see
[`docs/content/reference/compatibility.md`](docs/content/reference/compatibility.md).
