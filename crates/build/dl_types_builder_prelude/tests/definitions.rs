//! A miniature version of the definitions crate.
//!
//! The test is that this file compiles: it exercises every annotation `#[dalaran_type]` has to
//! strip, the `extern crate self as dalaran;` trick that makes `dalaran::`-rooted paths resolve with
//! no `use` statements anywhere, and the two prelude types that have no spelling in plain Rust.
//!
//! Several things in here would be hard errors without `#[dalaran_type]`: `#[dalaran(…)]` and friends
//! are registered nowhere, and `#[default]` normally requires a companion `#[derive(Default)]`.
//! `#[repr(…)]` is deliberately *not* stripped, so rustc still checks it.

extern crate self as dalaran;

pub use dl_types_builder_prelude::{Binary, f16, dalaran_type};

pub mod datatypes {
    /// A vector in 3D space.
    #[dalaran::dalaran_type]
    #[dalaran(state = "stable")]
    #[rust(derive(Default, Copy, bytemuck::Pod, bytemuck::Zeroable))]
    #[arrow(transparent)]
    #[repr(transparent)]
    pub struct Vec3D {
        pub xyz: [f32; 3],
    }

    /// The types the frontend has to be able to spell, including the prelude's own.
    #[dalaran::dalaran_type]
    #[dalaran(state = "unstable")]
    #[rust(derive_only(Clone, PartialEq))]
    pub enum TensorBuffer {
        /// 8bit unsigned integer.
        U8(Vec<u8>),

        /// 16bit IEEE-754 floating point, also known as `half`.
        F16(Vec<dalaran::f16>),

        /// A list of bytes of arbitrary length.
        Bytes(dalaran::Binary),
    }

    /// A C-style enum, with an explicit wire value per variant.
    #[dalaran::dalaran_type]
    #[dalaran(state = "stable")]
    #[repr(u8)]
    pub enum ColorModel {
        /// Red, green, blue.
        #[default]
        Rgb = 1,

        /// Red, green, blue, alpha.
        Rgba = 2,
    }
}

pub mod components {
    /// A position in 3D space.
    #[dalaran::dalaran_type]
    #[dalaran(state = "stable")]
    #[python(aliases = "npt.NDArray[Any] | Sequence[float]")]
    pub struct Position3D(pub dalaran::datatypes::Vec3D);
}

pub mod archetypes {
    /// A 3D point cloud with positions and optional colors, radii, labels, etc.
    #[dalaran::dalaran_type]
    #[dalaran(state = "stable")]
    #[docs(category = "Spatial 3D", view_types = "Spatial3DView")]
    pub struct Points3D {
        /// All the 3D positions at which the point cloud shows points.
        #[dalaran(required)]
        pub positions: Vec<dalaran::components::Position3D>,

        /// Which color model the point cloud is in, if any.
        #[dalaran(optional)]
        #[cpp(rename_field = "color_model_")]
        pub color_model: Option<dalaran::datatypes::ColorModel>,
    }
}

/// A definition file is never linked into anything, so there is nothing to assert at runtime —
/// compiling this file *is* the test.
#[test]
fn definitions_compile() {}
