//! Most analytics events collected by the Dalaran Viewer are defined in this file.
//!
//! All events are defined in the `dl_analytics` crate: <https://github.com/Flaminis/Dalaran/blob/main/crates/utils/dl_analytics/src/event.rs>
//!
//! Analytics can be completely disabled with `dalaran analytics disable`,
//! or by compiling dalaran without the `analytics` feature flag.

pub mod event;
mod wsl;
