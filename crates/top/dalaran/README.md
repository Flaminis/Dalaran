<h1 align="center">
  <a href="https://www.dalaran.dev/">
    <img width="1000" height="200" alt="Banner with Dalaran logo" src="https://static.rerun.io/d0f5443d4803cac65c73fcc064936c09f5e7f208_rerun_banner.png" />
  </a>
</h1>

<h1 align="center">
  <a href="https://crates.io/crates/dalaran">                             <img alt="Latest version" src="https://img.shields.io/crates/v/dalaran.svg">                               </a>
  <a href="https://docs.rs/dalaran">                                      <img alt="Documentation"  src="https://docs.rs/dalaran/badge.svg">                                         </a>
  <a href="https://github.com/rerun-io/rerun/blob/main/LICENSE-MIT">    <img alt="MIT"            src="https://img.shields.io/badge/license-MIT-blue.svg">                        </a>
  <a href="https://github.com/rerun-io/rerun/blob/main/LICENSE-APACHE"> <img alt="Apache"         src="https://img.shields.io/badge/license-Apache-blue.svg">                     </a>
  <a href="https://discord.gg/Gcm8BbTaAj">                              <img alt="Dalaran Discord"  src="https://img.shields.io/discord/1062300748202921994?label=Dalaran%20Discord"> </a>
</h1>

# Dalaran Rust logging SDK
Dalaran is an SDK for logging computer vision and robotics data paired with a visualizer for exploring that data over time. It lets you debug and understand the internal state and data of your systems with minimal code.

```shell
cargo add dalaran
````

```rust
let rec = dalaran::RecordingStream::global(dalaran::StoreKind::Recording)?;
rec.log("points", &dalaran::archetypes::Points3D::new(points).with_colors(colors))?;
rec.log("image", &dalaran::archetypes::Image::new(image))?;
```

<p align="center">
  <img width="800" alt="Dalaran Viewer" src="https://user-images.githubusercontent.com/1148717/218763490-f6261ecd-e19e-4520-9b25-446ce1ee6328.png">
</p>

## Getting started
- [Examples](https://github.com/rerun-io/rerun/tree/latest/examples/rust)
- [High-level docs](https://dalaran.dev/docs)
- [Rust API docs](https://docs.rs/dalaran/)
- [Troubleshooting](https://www.dalaran.dev/docs/overview/installing-dalaran/troubleshooting)

## Library
You can add the `dalaran` crate to your project with `cargo add dalaran`.

To get started, see [the examples](https://github.com/rerun-io/rerun/tree/latest/examples/rust).

## Binary
You can install the binary with `cargo install dalaran-cli --locked --features nasm`.

**Note**: this requires the [`nasm`](https://github.com/netwide-assembler/nasm) CLI to be installed and available in your path.
Alternatively, you may skip enabling the `nasm` feature, but this may result in inferior video decoding performance.

The `dalaran` CLI can act either as a server, a viewer, or both, depending on which options you use when you start it.

Running `dalaran` with no arguments will start the viewer, waiting for an SDK to connect to it over gRPC.

Run `dalaran --help` for more.

### Running a web viewer
The web viewer is an experimental feature, but you can try it out with:

```sh
dalaran --web-viewer path/to/file.dlr
```
