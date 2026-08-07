use std::collections::HashMap;

use dl_log_types::StoreId;

use super::RawRrdManifest;

/// This is the payload that is carried in messages of type `::End` in DLR streams.
///
/// It keeps track of various useful information about the associated recording.
///
/// During normal operations, there can only be a single `::End` message in an DLR stream, and
/// therefore a single `RrdFooter`.
/// It is possible to break that invariant by concatenating streams using external tools,
/// e.g. by doing something like `cat *.dlr > all_my_recordings.dlr`.
/// Passing that stream back through Dalaran tools, e.g. `cat *.dlr | dalaran dlr merge > all_my_recordings.dlr`,
/// would once again guarantee that only one `::End` message is present though.
/// I.e. that invariant holds as long as one stays within our ecosystem of tools.
///
/// This is an application-level type, the associated transport-level type can be found
/// over at [`dl_protos::log_msg::v1alpha1::RrdFooter`].
#[derive(Default, Debug)]
pub struct RrdFooter {
    /// All the [`RawRrdManifest`]s that were found in this DLR footer.
    ///
    /// Each [`RawRrdManifest`] corresponds to one, and exactly one, DLR stream (i.e. recording).
    ///
    /// The order is unspecified.
    pub manifests: HashMap<StoreId, RawRrdManifest>,
}
