<h1 align="center">
  <a href="https://www.dalaran.dev/">
    <img width="1000" height="200" alt="Banner with Dalaran logo" src="https://static.rerun.io/d0f5443d4803cac65c73fcc064936c09f5e7f208_rerun_banner.png" />
  </a>
</h1>

<h1 align="center">
  <a href="https://crates.io/crates/dalaran-cli">                         <img alt="Latest version" src="https://img.shields.io/crates/v/dalaran-cli.svg">                            </a>
  <a href="https://docs.rs/dalaran-cli">                                  <img alt="Documentation"  src="https://docs.rs/dalaran-cli/badge.svg">                                      </a>
  <a href="https://github.com/Flaminis/Dalaran/blob/main/LICENSE">    <img alt="Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg">                        </a>
  <a href="https://github.com/Flaminis/Dalaran/blob/main/LICENSE"> <img alt="Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg">                     </a>
  <a href="https://discord.gg/Gcm8BbTaAj">                              <img alt="Dalaran Discord"  src="https://img.shields.io/discord/1062300748202921994?label=Dalaran%20Discord"> </a>
</h1>

## Dalaran command-line tool
You can install the binary with `cargo install dalaran-cli --locked --features nasm`.

**Note**: this requires the [`nasm`](https://github.com/netwide-assembler/nasm) CLI to be installed and available in your path.
Alternatively, you may skip enabling the `nasm` feature, but this may result in inferior video decoding performance.

The `dalaran` CLI can act either as a server, a viewer, or both, depending on which options you use when you start it.

Running `dalaran` with no arguments will start the viewer, waiting for an SDK to connect to it over gRPC.

Run `dalaran --help` for more.


## What is Dalaran?
- [Examples](https://github.com/Flaminis/Dalaran/tree/latest/examples/rust)
- [High-level docs](https://dalaran.dev/docs)
- [Rust API docs](https://docs.rs/dalaran/)
- [Troubleshooting](https://www.dalaran.dev/docs/overview/installing-dalaran/troubleshooting)


### Running a web viewer
```sh
dalaran --web-viewer path/to/file.dlr
```
