//! Lenses allow you to extract, transform, and restructure component data. They
//! are applied to chunks that contain the target component.
//!
//! See [`crate::lenses::Lens`] for more details and assumptions. One way to make use of lenses is
//! by using the [`crate::lenses::LensesSink`].

mod sink;

// Re-exports from dl_lenses.
// We should be careful not to expose too much implementation details here.
pub use dl_lenses::{
    CastTo, ChunkExt, DeriveLensBuilder, Lens, LensBuilderError, LensError, LensRuntimeError,
    Lenses, MutateLensBuilder, OutputMode, default_runtime, op,
};

pub use dl_lenses_core::Selector;

// We keep the sink in dl_sdk since it depends on LogSink.
pub use self::sink::LensesSink;
