//! Most analytics events collected by the Rerun Viewer are defined in this file.
//!
//! All events are defined in the `dl_analytics` crate: <https://github.com/rerun-io/rerun/blob/main/crates/utils/dl_analytics/src/event.rs>
//!
//! Analytics can be completely disabled with `rerun analytics disable`,
//! or by compiling rerun without the `analytics` feature flag.

pub mod event;
mod wsl;
