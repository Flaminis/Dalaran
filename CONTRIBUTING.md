# Contributing to Dalaran

Thanks for considering it. This guide covers how to get a working development
environment, what we expect from a change, and how to get it merged.

Dalaran is a hard fork of [Rerun](https://github.com/rerun-io/rerun) — see
[`ATTRIBUTION.md`](ATTRIBUTION.md). If you are fixing a bug that also exists
upstream, please consider sending it there too; we do the same.

## See also

* [`ROADMAP.md`](ROADMAP.md) — what we are planning, and what we are not
* [`BUILD.md`](BUILD.md) — building from source
* [`ARCHITECTURE.md`](ARCHITECTURE.md) — how the crates fit together
* [`CODE_STYLE.md`](CODE_STYLE.md) — style beyond what the formatters enforce
* [`TESTING.md`](TESTING.md) — the testing philosophy
* [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — how we behave
* [`SECURITY.md`](SECURITY.md) — how to report a vulnerability
* [`dalaran_py/README.md`](dalaran_py/README.md) — Python SDK build details

## Naming conventions

The fork renamed everything user-facing, and PRs are expected to follow it:

* Rust crates are `dl_*`; the umbrella crate is `dalaran` and the CLI crate is
  `dalaran-cli` (binary `dalaran`).
* The Python package is `dalaran` (distribution `dalaran-sdk`), aliased as
  `import dalaran as dl` and `import dalaran.blueprint as dlb`.
* The C API is prefixed `dl_`/`DL_`; the C++ namespace is `dalaran::`.
* Recordings are `.dlr`, blueprints `.dbl`, and URIs use the `dalaran://`
  scheme.

Do not reintroduce `rerun`/`re_` naming for anything of ours. Links to
`github.com/rerun-io/*`, `static.rerun.io` asset URLs, and the `RRF2` on-disk
fourcc are intentional and must stay — see [`ATTRIBUTION.md`](ATTRIBUTION.md).

## Development setup

We use [`pixi`](https://pixi.sh/) to pin and fetch dev tools, and
[`uv`](https://docs.astral.sh/uv/) for Python environments. Rust comes from the
toolchain pinned in [`rust-toolchain`](rust-toolchain). Python 3.10–3.12 is
supported.

```sh
git clone https://github.com/Flaminis/Dalaran.git
cd Dalaran
pixi run check-env      # verifies your environment is usable
pixi task list          # every task available, this is the source of truth
```

Common entry points:

```sh
pixi run dalaran            # build and run the viewer
pixi run dalaran-cli --help # the CLI without rebuilding the viewer
pixi run py-build           # build the Python SDK into the uv environment
pixi run -e cpp cpp-build-all
```

Install the pre-push hook so lint failures surface before CI does:

```sh
git config core.hooksPath hooks
```

### Tests

```sh
cargo nextest run --all-targets --all-features   # Rust (or `cargo test`)
cargo test --all-features --doc                  # Rust doc tests
pixi run py-test                                 # Python, pytest under dalaran_py/tests
pixi run -e cpp cpp-test                         # C++, catch2
```

Some Rust tests are [`insta`](https://docs.rs/insta) snapshot tests; review
changes with `cargo insta review`. Some render an image and compare it against
a checked-in reference; regenerate with `UPDATE_SNAPSHOTS=1` and inspect
failures with `pixi run snapshots`. Image tests need a `wgpu`-capable driver
(Vulkan or Metal), so they may not run in every environment — say so in the PR
if you could not run them locally.

Run at least the suites your change touches, and prefer adding a test to
describing manual steps.

### Linting

```sh
pixi run fast-lint
```

Run it before you push. It is seconds on repeated runs. Rust is formatted with
`cargo fmt`, Python with `ruff`, and there is a repo-wide `scripts/lint.py`
with project-specific rules — configure your editor to format on save, strip
trailing whitespace, and end files with a newline.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) subjects:

```
feat(robot): add Robot high-level logging handle
fix(dl_chunk): correct row-id ordering for static components
docs(readme): document the .dlrpack bundle format
test(dl_tf): cover frame resolution with a missing parent
```

Common scopes are the crate or module you touched (`dl_viewer`, `dl_chunk`,
`sdk-python`, `cpp`, `docs`, `ci`).

The body should explain **why** the change is being made, in complete
sentences. A reviewer can read the diff to see what changed; they cannot read
your mind about the reason. Keep commits small and individually coherent — a
branch of five reviewable commits is much easier to merge than one large one.

### Sign-off (DCO)

Every commit must carry a `Signed-off-by` line certifying the
[Developer Certificate of Origin](https://developercertificate.org/) — that you
wrote the change, or have the right to submit it under Apache-2.0:

```sh
git commit -s -m "fix(dl_tf): resolve frames with a missing parent"
```

which appends:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use your real name and an email you can be reached at. If you forgot, fix the
last commit with `git commit --amend -s`, or a whole branch with
`git rebase --signoff main`. We do not require a separate CLA; the DCO is the
only paperwork.

### Licensing of contributions

Contributions are accepted under the [Apache License, Version 2.0](LICENSE).
Do not add code under a copyleft licence, do not paste MIT or GPL headers into
files, and be careful with generated code whose provenance you cannot state.
New dependencies must be Apache-2.0-compatible; `cargo deny check` enforces
this and runs in CI.

## Pull requests

We use short-lived branches off `main`.

* Do not open a PR from your own `main` branch — reviewers cannot push fixes to
  it.
* Add review feedback as new commits rather than force-pushing, so reviewers can
  follow what changed. PRs are squash-merged, so branch history need not be
  pretty.
* Open as a draft if you want early feedback on the design; un-draft when you
  have read your own diff and think it is ready.
* Fill in [the PR template](.github/PULL_REQUEST_TEMPLATE.md). Say why the
  change exists, what you want reviewed, and how confident you are.
* Include a screenshot or a short video for anything visual.

### Size and scope

Maintainer review time is the scarce resource. Please keep a PR to either:

* a small, self-contained change, or
* a larger change that you have discussed with a maintainer first, in an issue.

Large undiscussed rewrites are likely to sit unreviewed, which wastes your time
more than ours.

### Agent-assisted contributions

Coding agents are fine as tools, but you are the author. If you used one, say
so in the PR description, be able to explain the solution in your own words,
and read the diff yourself before un-drafting. PRs that are obviously
machine-generated and unreviewed may be closed without detailed feedback.

### Adding dependencies

Every dependency costs compile time, binary size, attack surface, and future
breakage. Sometimes a hundred lines of code is the better trade. When you add
one, justify it in the PR: why not write it ourselves, and why this crate over
the alternatives. For Rust, prefer `default-features = false`. Check the
`Cargo.lock` diff (GitHub collapses it). A full `cargo update` belongs in its
own PR.

## Proposing a feature

1. Search [existing issues](https://github.com/Flaminis/Dalaran/issues) and
   [`ROADMAP.md`](ROADMAP.md) first.
2. Open a **Feature request** issue describing the problem you have, the
   workaround you are using today, and only then your proposed solution. The
   problem statement is the part we most need.
3. For anything touching a public API, a data format, or the viewer's
   interaction model, wait for a maintainer to agree on the shape before
   writing the implementation. This is not bureaucracy: API and format
   decisions are expensive to undo.
4. If your feature is a robotics integration — a message type, a bag format, a
   frame convention — use the **Robotics integration** issue template and
   include a small sample recording or bag if you can.

Examples are always welcome; follow the pattern of what is already in
[`examples/`](examples).

## Reporting bugs

Use the **Bug report** template and include the output of:

```sh
dalaran --version
```

plus your OS, GPU and driver, and the SDK language and version. A minimal
reproduction — ideally a short script and a small `.dlr` file — is worth more
than a long description.

## Reporting security issues

Do **not** open a public issue for a vulnerability. Email
<opensource@dalaran.dev>, or use GitHub's private reporting on the Security
tab; [`SECURITY.md`](SECURITY.md) has the details of what to include and what
to expect.

## Repository structure

Rust crates live in [`crates/`](crates), grouped into `top`, `store`, `viewer`,
`utils`, and `build`. Language bindings are in [`dalaran_py/`](dalaran_py),
[`dalaran_cpp/`](dalaran_cpp), and [`dalaran_js/`](dalaran_js). Docs are in
[`docs/content/`](docs/content), cross-language snippets in
[`docs/snippets/`](docs/snippets), and examples in [`examples/`](examples).

For an overview of the Rust APIs:

```sh
cargo doc --no-deps --open
```

## Debugging tips

* `export RUST_LOG=trace` for verbose logging; debug logging is enabled
  automatically for the viewer when run from inside a Dalaran checkout.
* [`bacon`](https://github.com/Canop/bacon) re-runs `cargo clippy` on save; see
  [`bacon.toml`](bacon.toml).
* [`sccache`](https://github.com/mozilla/sccache) makes branch switching much
  less painful.
