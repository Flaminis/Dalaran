# dl_types_builder

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_types_builder.svg)](https://crates.io/crates/dl_types_builder)
[![Documentation](https://docs.rs/dl_types_builder/badge.svg)](https://docs.rs/dl_types_builder)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

This crate implements Dalaran's code generation tools.

These tools translate language-agnostic IDL definitions (flatbuffers) into code.

You can generate the code with `pixi run codegen`.

### Doclinks

The `.fbs` files can contain docstring (`///`) which in turn can contain doclinks.
They are to be written on the form `[archetypes.Image]`.

Only links to types are currently supported.

Link checking is not done by the codegen, but the output is checked implicitly by `cargo doc`, `lychee` etc.

We only support doclinks to the default `dalaran.scope`.
