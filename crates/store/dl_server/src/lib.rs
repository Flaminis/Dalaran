#![allow(clippy::iter_over_hash_type)]

//! A Dalaran server implementation backed by an in-memory store.

#[cfg(not(target_arch = "wasm32"))]
mod entrypoint;
#[cfg(not(target_arch = "wasm32"))]
mod layers;
mod named_path;
mod dalaran_cloud;
#[cfg(not(target_arch = "wasm32"))]
mod server;
mod store;

pub use self::named_path::{NamedPath, NamedPathCollection};
pub use self::dalaran_cloud::{
    DalaranCloudHandler, DalaranCloudHandlerBuilder, DalaranCloudHandlerSettings,
};
#[cfg(not(target_arch = "wasm32"))]
pub use self::{
    entrypoint::Args,
    layers::InjectedErrors,
    server::{Server, ServerBuilder, ServerError, ServerHandle},
};

/// What should we do on error?
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum OnError {
    Continue,
    Abort,
}
