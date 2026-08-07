# CI workflows

Dalaran is an independent, Apache-2.0 fork of [Rerun](https://github.com/rerun-io/rerun).
The fork inherited about fifty workflows from upstream, essentially all of which were
wired to infrastructure that only exists inside the upstream organisation. This document
records what was kept, what was deleted, and why.

The guiding rule: **every workflow here must be green on a stock GitHub-hosted runner,
for a contributor who has no repository secrets at all.** Anything that cannot satisfy
that either becomes an opt-in manual job or does not live here.

## What runs today

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | push/PR to `main` | `cargo fmt --check`, clippy (store + utility crates, `--deny warnings`), `cargo check --workspace --locked`, `cargo test` on the fast crates |
| `python.yml` | push/PR to `main` | `ruff format --check`, `ruff check`, `mypy`, and `pytest dalaran_py/tests/unit` on Python 3.10, 3.11 and 3.12 |
| `cpp.yml` | push/PR touching C++ or CMake | configures `dalaran_cpp` and builds the `dalaran_sdk` target with CMake + Ninja |
| `docs.yml` | push/PR touching docs or the SDK | lychee link check, doc-redirect check, `mkdocs build --strict` for the Python API reference |
| `release.yml` | `v*` tags, `workflow_dispatch` | builds wheels, packages crates, packs the npm viewer; publishing is manual and secret-gated |

Shared conventions, applied to all of them:

- `permissions:` is declared explicitly and is `contents: read` unless a job needs more.
- Every workflow has a `concurrency:` group so a new push cancels the stale run
  (except `release.yml`, where cancelling a half-finished publish would be worse).
- Actions are pinned to a version tag, never to a floating branch.
- The Rust toolchain comes from the `rust-toolchain` file via plain `rustup`, so CI and
  a local checkout always agree on the compiler.
- Rust caching uses `Swatinem/rust-cache` and only writes from `main`, so pull requests
  read a warm cache without evicting each other's entries.

## Required repository secrets

None of the day-to-day workflows need a secret. `release.yml` uses three, all optional;
each one only unlocks its own job, and the job degrades to a dry run when it is missing.

| Secret | Used by | Purpose |
| --- | --- | --- |
| `PYPI_API_TOKEN` | `release.yml` → `publish-wheels` | Uploads the `dalaran-sdk` wheels to PyPI. |
| `CARGO_REGISTRY_TOKEN` | `release.yml` → `crates` | `cargo publish` for the `dl_*`, `dalaran` and `dalaran-cli` crates. |
| `NPM_TOKEN` | `release.yml` → `npm` | `npm publish` for the web viewer packages. |

`GITHUB_TOKEN` is the automatic per-run token; it is only used to raise the rate limit
when downloading protoc.

## Cutting a release

1. Bump the versions and land the changelog on `main`.
2. Push a `v*` tag. The tag push packages everything and publishes nothing.
3. Check the artifacts of that run.
4. Re-run `release.yml` from the Actions tab via **Run workflow** with `dry_run` unchecked.
   Only the jobs whose secret is configured will publish.

## What was deleted, and why

### Google Cloud / build artifact infrastructure

`reusable_build_and_upload_dalaran_c.yml`, `reusable_build_and_upload_dalaran_cli.yml`,
`reusable_build_and_upload_wheels.yml`, `reusable_bundle_and_upload_dalaran_cpp.yml`,
`reusable_upload_examples.yml`, `reusable_upload_js.yml`, `reusable_upload_web.yml`,
`reusable_publish_dalaran_c.yml`, `reusable_publish_dalaran_cli.yml`,
`reusable_publish_js.yml`, `reusable_publish_web.yml`, `reusable_publish_wheels.yml`,
`reusable_pip_index.yml`, `reusable_sync_release_assets.yml`, `adhoc_wheels.yml`.

All of these authenticate to Google Cloud through workload identity federation and read
or write `build.rerun.io` / `static.rerun.io` buckets. We have neither the identity pool
nor the buckets. Release packaging that we can actually run lives in `release.yml`.

### sccache and self-hosted runners

`.github/actions/setup-rust`, `.github/scripts/setup_sccache.sh` and `.github/runs-on.yml`.

The composite action set up GCP credentials as a side effect and pointed sccache at a GCS
bucket; `runs-on.yml` described an AWS-backed self-hosted runner fleet (`x64-ubuntu-large`,
`arm64-ubuntu-small`, …) that a fork cannot schedule onto. Every job here uses
`ubuntu-latest` and `Swatinem/rust-cache` instead.

### Deployment and preview infrastructure

`reusable_deploy_docs.yml`, `reusable_deploy_landing_preview.yml`, `on_push_docs.yml`,
`auto_docs.yml`, `auto_docs_check.yml`, `.github/actions/vercel`.

These deploy to upstream's Vercel projects, their documentation site and their landing
repository, using Vercel tokens and cross-repository dispatch tokens. Nothing to point
them at. `docs.yml` keeps the part that is verification rather than deployment.

### Bots that need elevated tokens

`auto_approve.yml`, `checkboxes.yml`, `first_time_contrib.yml`, `on_pr_comment.yml`,
`labels.yml`, `enforce_branch_name.yml`, `update_kittest_snapshots.yml`,
`notify-reality-sync.yml`, `pr-trigger-reality-sync.yml`.

These post comments, push labels, approve runs, push snapshot commits back to pull
request branches or dispatch into a private "reality sync" repository. They rely on a
GitHub App or a personal access token belonging to the upstream organisation, and several
of them use `pull_request_target`, which is a privilege-escalation footgun that is not
worth carrying for a bot we cannot run anyway.

### Cloud benchmarks, size tracking and analytics

`reusable_bench.yml`, `reusable_track_size.yml`, `nightly.yml`.

Benchmark and binary-size history is written to upstream's buckets and rendered by their
dashboards; the nightly job additionally builds and uploads release artifacts for every
platform. Reintroducing performance tracking is worthwhile, but it needs storage we have
to choose first.

### Orchestration wrappers

`on_pull_request.yml`, `on_pull_request_contrib.yml`, `on_push_main.yml`,
`on_gh_release.yml`, `release.yml` (the upstream one), `contrib_checks.yml`,
`contrib_dalaran_py.yml`, `reusable_checks.yml`, `reusable_checks_rust.yml`,
`reusable_checks_python.yml`, `reusable_checks_cpp.yml`, `reusable_build_examples.yml`,
`reusable_build_js.yml`, `reusable_build_web.yml`, `reusable_run_notebook.yml`,
`reusable_test_wheels.yml`, `reusable_web_test.yml`, `reusable_release_crates.yml`,
`clear_cache.yml`, `cargo_shear.yml`, `reusable_checks_protobuf.yml`,
`reusable_checks_doc_redirects.yml`, plus the `cpp_matrix_full.json` and
`lsan_suppressions.supp` data files.

These are the fan-out layer: a dozen reusable workflows called with a shared concurrency
token, most of which transitively depend on one of the categories above, and all of which
are driven by `pixi` environments that take tens of minutes to resolve on a cold runner.
The checks that survive without that machinery — rustfmt, clippy, `cargo check`, ruff,
mypy, pytest, the CMake build, doc redirects and link checking — have been rewritten
directly in the five workflows listed at the top. The doc-redirect check in particular
was kept and now lives in `docs.yml`.

Worth restoring later, in rough order of value: `cargo_shear` (unused-dependency
detection, needs no secrets), the protobuf breaking-change check via `buf`, the C++
matrix build across compilers, and the wasm/web viewer build.

### What upstream files were kept

`.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md` carry no infrastructure
assumptions and were left as they are.

## Adding a workflow

- Validate the YAML before pushing: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/<name>.yml'))"`.
- Set `permissions:` to the narrowest set that works, and add a `concurrency:` group.
- Pin every action to a version tag.
- If it needs a secret, it must degrade to a no-op — not a failure — when that secret is
  absent, the way `release.yml` does.
