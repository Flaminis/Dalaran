use std::path::PathBuf;

use anyhow::Context as _;
use crossbeam::channel;
use dl_chunk::external::crossbeam;
use dl_log_encoding::RawRrdManifest;
use dl_quota_channel::send_crossbeam;
use itertools::Itertools as _;

// ---

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum InputSource {
    Stdin,
    File(PathBuf),
}

impl std::fmt::Display for InputSource {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Stdin => write!(f, "stdin"),
            Self::File(path) => write!(f, "{path:?}"),
        }
    }
}

/// Asynchronously decodes potentially multiplexed DLR streams from the given `paths`, or standard
/// input if none are specified.
///
/// This function returns 2 channels:
/// * The first channel contains both the successfully decoded data, if any, as well as any
///   errors faced during processing.
/// * The second channel, which will fire only once, after all processing is done, indicates the
///   total number of bytes processed, and returns all DLR manifests that were parsed from footers
///   in the underlying stream.
///
/// This function is best-effort: it will try to make progress even in the face of errors.
/// It is up to the user to decide whether and when to stop.
///
/// This function is capable of decoding multiple independent recordings from a single stream.
#[expect(clippy::type_complexity)] // internal private API for the CLI impl
pub fn read_dlr_streams_from_file_or_stdin(
    paths: &[String],
) -> (
    channel::Receiver<(InputSource, anyhow::Result<dl_log_types::LogMsg>)>,
    channel::Receiver<(u64, Vec<(InputSource, anyhow::Result<RawRrdManifest>)>)>,
) {
    read_any_dlr_streams_from_file_or_stdin::<dl_log_types::LogMsg>(paths)
}

/// Asynchronously decodes potentially multiplexed DLR streams from the given `paths`, or standard
/// input if none are specified.
///
/// This only decodes from raw bytes up to transport-level types (i.e. Protobuf payloads are
/// decoded, but Arrow data is never touched).
///
/// This function returns 2 channels:
/// * The first channel contains both the successfully decoded data, if any, as well as any
///   errors faced during processing.
/// * The second channel, which will fire only once, after all processing is done, indicates the
///   total number of bytes processed, and returns all DLR manifests that were parsed from footers
///   in the underlying stream.
///
/// This function is best-effort: it will try to make progress even in the face of errors.
/// It is up to the user to decide whether and when to stop.
///
/// This function is capable of decoding multiple independent recordings from a single stream.
//
// TODO(#10730): if the legacy `StoreId` migration is removed from `Decoder`, this would break
// the ability for this function to use pre-0.25 rrds. If we want to keep the ability to migrate
// here, then the pre-#10730 app id caching mechanism must somehow be ported here.
// TODO(ab): For pre-0.25 legacy data with `StoreId` missing their application id, the migration
// in `Decoder` requires `SetStoreInfo` to arrive before the corresponding `ArrowMsg`. Ideally
// this tool would cache orphan `ArrowMsg` until a matching `SetStoreInfo` arrives.
#[expect(clippy::type_complexity)] // internal private API for the CLI impl
pub fn read_raw_dlr_streams_from_file_or_stdin(
    paths: &[String],
) -> (
    channel::Receiver<(
        InputSource,
        anyhow::Result<dl_protos::log_msg::v1alpha1::log_msg::Msg>,
    )>,
    channel::Receiver<(u64, Vec<(InputSource, anyhow::Result<RawRrdManifest>)>)>,
) {
    read_any_dlr_streams_from_file_or_stdin::<dl_protos::log_msg::v1alpha1::log_msg::Msg>(paths)
}

#[expect(clippy::type_complexity)] // internal private API for the CLI impl
fn read_any_dlr_streams_from_file_or_stdin<
    T: dl_log_encoding::DecoderEntrypoint + Send + std::fmt::Debug + 'static,
>(
    paths: &[String],
) -> (
    channel::Receiver<(InputSource, anyhow::Result<T>)>,
    channel::Receiver<(u64, Vec<(InputSource, anyhow::Result<RawRrdManifest>)>)>,
) {
    let path_to_input_rrds = paths
        .iter()
        .filter(|s| !s.is_empty()) // Avoid a problem with `pixi run check-backwards-compatibility`
        .map(PathBuf::from)
        .collect_vec();

    // TODO(cmc): might want to make this configurable at some point.
    let (tx_msgs, rx_msgs) = crossbeam::channel::bounded(100);
    let (tx_metadata, rx_metadata) = crossbeam::channel::bounded(1);

    _ = std::thread::Builder::new()
        .name("dalaran-dlr-in".to_owned())
        .spawn(move || {
            let mut dlr_manifests = Vec::new();
            let mut size_bytes = 0;

            if path_to_input_rrds.is_empty() {
                // stdin

                let source = InputSource::Stdin;
                let stdin = std::io::BufReader::new(std::io::stdin().lock());
                let mut decoder = dl_log_encoding::Decoder::decode_lazy(stdin);

                for res in &mut decoder {
                    let res = res.context("couldn't decode message from stdin -- skipping");
                    send_crossbeam(&tx_msgs, (source.clone(), res)).ok();
                }

                size_bytes += decoder.num_bytes_processed();

                match decoder.dlr_manifests().context("couldn't decode footers") {
                    Ok(v) => dlr_manifests.extend(v.into_iter().map(|m| (source.clone(), Ok(m)))),
                    Err(err) => dlr_manifests.push((source.clone(), Err(err))),
                }
            } else {
                // file(s)

                for dlr_path in path_to_input_rrds {
                    let dlr_file = match std::fs::File::open(&dlr_path)
                        .with_context(|| format!("couldn't open {dlr_path:?} -- skipping"))
                    {
                        Ok(file) => file,
                        Err(err) => {
                            send_crossbeam(
                                &tx_msgs,
                                (InputSource::File(dlr_path.clone()), Err(err)),
                            )
                            .ok();
                            continue;
                        }
                    };

                    let source = InputSource::File(dlr_path.clone());
                    let dlr_file = std::io::BufReader::new(dlr_file);
                    let mut decoder = dl_log_encoding::Decoder::decode_lazy(dlr_file);
                    for res in &mut decoder {
                        let res = res.context("decode dlr message").with_context(|| {
                            format!("couldn't decode message {dlr_path:?} -- skipping")
                        });
                        send_crossbeam(&tx_msgs, (source.clone(), res)).ok();
                    }

                    size_bytes += decoder.num_bytes_processed();

                    match decoder.dlr_manifests().context("couldn't decode footers") {
                        Ok(v) => {
                            dlr_manifests.extend(v.into_iter().map(|m| (source.clone(), Ok(m))));
                        }
                        Err(err) => dlr_manifests.push((source.clone(), Err(err))),
                    }
                }
            }

            send_crossbeam(&tx_metadata, (size_bytes, dlr_manifests)).ok();
        });

    (rx_msgs, rx_metadata)
}
