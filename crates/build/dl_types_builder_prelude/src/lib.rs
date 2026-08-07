//! The vocabulary that Dalaran's IDL definitions are written against.
//!
//! Dalaran's type definitions are a subset of Rust that is parsed by `dl_types_builder` and *also*
//! compiled by rustc, purely so that we get name resolution, typo-checking, rust-analyzer and
//! `cargo fmt` for free. The definitions crate is never linked into anything.
//!
//! Definitions refer to each other by their fully-qualified name with `.` swapped for `::`
//! — `dalaran.components.Position3D` is written `dalaran::components::Position3D` — and never
//! contain a `use` statement. A single `extern crate self as dalaran;` in the definitions crate's
//! generated `lib.rs` makes that resolve in every module.
//!
//! For that rule to hold without exceptions, every name a definition can mention has to live
//! under `dalaran::`, including the two that have no spelling in plain Rust. Hence this crate:
//! the definitions crate re-exports [`Binary`] and [`struct@f16`] at its own root, so they are
//! written `dalaran::Binary` and `dalaran::f16` like everything else.

pub use half::f16;

pub use dl_types_builder_macros::dalaran_type;

/// A list of bytes of arbitrary length — the Arrow `Binary` type.
///
/// Written `dalaran::Binary` in a definition. This is a name for the frontend to recognize, not a
/// type anyone constructs; the generated code uses the target language's own byte-buffer type.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Binary;
