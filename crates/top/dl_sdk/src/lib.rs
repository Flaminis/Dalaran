//! The Dalaran logging SDK
//!
//! This is the bare-bones version of the [`dalaran`](https://docs.rs/dalaran/) crate.
//! `dalaran` exports everything in `dl_sdk`, so in most cases you want to use `dalaran`
//! instead.
//!
//! Please read [the docs for the `dalaran` crate](https://docs.rs/dalaran/) instead.
//!
//! ## Feature flags
#![doc = document_features::document_features!()]
//!

#![warn(missing_docs)] // Let's keep the this crate well-documented!

// ----------------
// Private modules:

mod binary_stream_sink;
mod global;
mod log_sink;
mod recording_stream;
mod spawn;

// ---------------
// Public modules:

pub mod blueprint;

// -------------
// Public items:

pub use spawn::{SpawnError, SpawnOptions, spawn};

pub use self::recording_stream::{
    RecordingStream, RecordingStreamBuilder, RecordingStreamError, RecordingStreamResult,
    forced_sink_path,
};

/// The default port of a Dalaran gRPC /proxy server.
pub const DEFAULT_SERVER_PORT: u16 = dl_uri::DEFAULT_PROXY_PORT;

/// The default URL of a Dalaran gRPC /proxy server.
///
/// This isn't used to _host_ the server, only to _connect_ to it.
pub const DEFAULT_CONNECT_URL: &str =
    const_format::concatcp!("dalaran+http://127.0.0.1:", DEFAULT_SERVER_PORT, "/proxy");

pub use dl_log_types::{
    ApplicationId, EntityPath, EntityPathFilter, EntityPathPart, Instance, StoreId, StoreKind,
    entity_path,
};
pub use dl_sdk_types::archetypes::RecordingInfo;
pub use global::cleanup_if_forked_child;

#[cfg(not(target_arch = "wasm32"))]
impl crate::sink::LogSink for dl_log_encoding::FileSink {
    fn send(&self, msg: dl_log_types::LogMsg) {
        Self::send(self, msg);
    }

    #[inline]
    fn flush_blocking(&self, timeout: std::time::Duration) -> Result<(), sink::SinkFlushError> {
        use dl_log_encoding::FileFlushError;

        Self::flush_blocking(self, timeout).map_err(|err| match err {
            FileFlushError::Failed { message } => sink::SinkFlushError::Failed { message },
            FileFlushError::Timeout => sink::SinkFlushError::Timeout,
        })
    }

    #[inline]
    fn defers_finalization_to_shutdown(&self) -> bool {
        true
    }
}

// ---------------
// Public modules:

/// Different destinations for log messages.
///
/// This is how you select whether the log stream ends up
/// sent over gRPC, written to file, etc.
pub mod sink {
    #[cfg(not(target_arch = "wasm32"))]
    pub use dl_log_encoding::{FileSink, FileSinkError, FileSinkOptions};

    pub use crate::binary_stream_sink::{BinaryStreamSink, BinaryStreamStorage};
    pub use crate::log_sink::{
        BufferedSink, CallbackSink, GrpcSink, GrpcSinkConnectionFailure, GrpcSinkConnectionState,
        IntoMultiSink, LogSink, MemorySink, MemorySinkStorage, MultiSink, SinkFlushError,
    };
}

/// Things directly related to logging.
pub mod log {
    pub use dl_chunk::{
        Chunk, ChunkBatcher, ChunkBatcherConfig, ChunkBatcherError, ChunkBatcherResult,
        ChunkComponents, ChunkError, ChunkId, ChunkResult, PendingRow, RowId, TimeColumn,
    };
    pub use dl_log_types::LogMsg;
}

/// Time-related types.
pub mod time {
    pub use dl_log_types::{
        Duration, TimeCell, TimeInt, TimePoint, TimeType, Timeline, TimelineName, Timestamp,
    };
}

pub use dl_sdk_types::{
    Archetype, ArchetypeName, AsComponents, Component, ComponentBatch, ComponentDescriptor,
    ComponentIdentifier, ComponentType, DeserializationError, DeserializationResult, Loggable,
    SerializationError, SerializationResult, SerializedComponentBatch, SerializedComponentColumn,
};
pub use time::{TimeCell, TimePoint, Timeline, TimelineName};

/// Transformation and reinterpretation of components.
///
/// # Experimental
///
/// This is an experimental API and may change in future releases.
pub mod lenses;

pub use dl_byte_size::SizeBytes;
#[cfg(feature = "importers")]
pub use dl_importer::{ImportedData, Importer, ImporterError, ImporterSettings};

#[cfg(feature = "importers")]
#[deprecated(since = "0.32.0", note = "Renamed to `Importer`.")]
#[doc(hidden)]
pub use dl_importer::Importer as DataLoader;
#[cfg(feature = "importers")]
#[deprecated(since = "0.32.0", note = "Renamed to `ImporterError`.")]
#[doc(hidden)]
pub type DataLoaderError = dl_importer::ImporterError;
#[cfg(feature = "importers")]
#[deprecated(since = "0.32.0", note = "Renamed to `ImporterSettings`.")]
#[doc(hidden)]
pub type DataLoaderSettings = dl_importer::ImporterSettings;
#[cfg(feature = "importers")]
#[deprecated(since = "0.32.0", note = "Renamed to `ImportedData`.")]
#[doc(hidden)]
pub type LoadedData = dl_importer::ImportedData;

/// Methods for spawning the web viewer and streaming the SDK log stream to it.
#[cfg(feature = "web_viewer")]
pub mod web_viewer;

/// Method for spawning a gRPC server and streaming the SDK log stream to it.
#[cfg(feature = "server")]
pub mod grpc_server;

#[cfg(feature = "server")]
pub use dl_grpc_server::{MemoryLimit, PlaybackBehavior, ServerOptions};

/// Re-exports of other crates.
pub mod external {
    pub use dl_chunk::external::*;
    #[cfg(feature = "server")]
    pub use dl_grpc_server;
    #[cfg(feature = "importers")]
    pub use dl_importer::{self, external::*};
    pub use dl_log::external::*;
    pub use dl_log_types::external::*;
    pub use {dl_grpc_client, dl_log, dl_log_encoding, dl_log_types, dl_uri};
}

#[cfg(feature = "web_viewer")]
pub use web_viewer::serve_web_viewer;

// -----
// Misc:

/// The version of the Dalaran SDK.
pub fn build_info() -> dl_build_info::BuildInfo {
    dl_build_info::build_info!()
}

const DALARAN_ENV_VAR: &str = "DALARAN";

/// Helper to get the value of the `DALARAN` environment variable.
fn get_dalaran_env() -> Option<bool> {
    let s = std::env::var(DALARAN_ENV_VAR).ok()?;
    match s.to_lowercase().as_str() {
        "0" | "false" | "off" => Some(false),
        "1" | "true" | "on" => Some(true),
        _ => {
            dl_log::warn!(
                "Invalid value for environment variable {DALARAN_ENV_VAR}={s:?}. Expected 'on' or 'off'. It will be ignored"
            );
            None
        }
    }
}

/// Checks the `DALARAN` environment variable. If not found, returns the argument.
///
/// Also adds some helpful logging.
pub fn decide_logging_enabled(default_enabled: bool) -> bool {
    // We use `info_once` so that we can call this function
    // multiple times without spamming the log.
    match get_dalaran_env() {
        Some(true) => {
            dl_log::info_once!(
                "Dalaran Logging is enabled by the '{DALARAN_ENV_VAR}' environment variable."
            );
            true
        }
        Some(false) => {
            dl_log::info_once!(
                "Dalaran Logging is disabled by the '{DALARAN_ENV_VAR}' environment variable."
            );
            false
        }
        None => {
            if !default_enabled {
                dl_log::info_once!(
                    "Dalaran Logging has been disabled. Turn it on with the '{DALARAN_ENV_VAR}' environment variable."
                );
            }
            default_enabled
        }
    }
}

// ----------------------------------------------------------------------------

/// Creates a new [`dl_log_types::StoreInfo`] which can be used with [`RecordingStream::new`].
#[track_caller] // track_caller so that we can see if we are being called from an official example.
pub fn new_store_info(
    application_id: impl Into<dl_log_types::ApplicationId>,
) -> dl_log_types::StoreInfo {
    let store_id = StoreId::random(StoreKind::Recording, application_id.into());

    dl_log_types::StoreInfo::new(
        store_id,
        dl_log_types::StoreSource::RustSdk {
            rustc_version: env!("RE_BUILD_RUSTC_VERSION").into(),
            llvm_version: env!("RE_BUILD_LLVM_VERSION").into(),
        },
    )
}
