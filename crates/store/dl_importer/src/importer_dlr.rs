use dl_log_encoding::Decoder;
use dl_log_types::ApplicationId;

use crate::{ImportedData, Importer as _};

// ---

/// Imports data from any `dlr` file or in-memory contents.
pub struct RrdImporter;

impl crate::Importer for RrdImporter {
    #[inline]
    fn name(&self) -> String {
        "dalaran.importers.Dlr".into()
    }

    #[cfg(not(target_arch = "wasm32"))]
    fn import_from_path(
        &self,
        settings: &crate::ImporterSettings,
        filepath: std::path::PathBuf,
        tx: crossbeam::channel::Sender<crate::ImportedData>,
    ) -> Result<(), crate::ImporterError> {
        use anyhow::Context as _;

        dl_tracing::profile_function!(filepath.display().to_string());

        let mut extension = normalize_extension(&crate::extension(&filepath), &filepath);
        if !matches!(extension.as_str(), "dbl" | "dlr") {
            if filepath.is_file() || filepath.is_dir() {
                // NOTE: blueprints and recordings have the same file format
                return Err(crate::ImporterError::Incompatible(filepath.clone()));
            } else {
                // NOTE(1): If this is some kind of virtual file (fifo, socket, pipe, etc), then we
                // always assume it's an DLR stream by default.
                //
                // NOTE(2): Because waiting for an end-of-stream marker on a pipe doesn't make sense,
                // we tag it as `dbl` instead of `dlr` (but really this just means: please don't block
                // indefinitely).
                extension = "dbl".to_owned();
            }
        }

        dl_log::debug!(
            ?filepath,
            importer = self.name(),
            "Loading dlr data from filesystem…",
        );

        match extension.as_str() {
            "dbl" => {
                // We assume .dbl is not streamed and no retrying after seeing EOF is needed.
                // Otherwise we'd risk retrying to read .dbl file that has no end-of-stream header and
                // blocking the UI update thread indefinitely and making the viewer unresponsive (as .dbl
                // files are sometimes read on UI update).
                let file = std::fs::File::open(&filepath)
                    .with_context(|| format!("Failed to open file {filepath:?}"))?;
                let file = std::io::BufReader::new(file);

                let messages = Decoder::decode_eager(file)?;

                // NOTE: This is IO bound, it must run on a dedicated thread, not the shared rayon thread pool.
                std::thread::Builder::new()
                    .name(format!("decode_and_stream({filepath:?})"))
                    .spawn({
                        let filepath = filepath.clone();
                        let settings = settings.clone();
                        move || {
                            decode_and_stream(
                                &filepath,
                                &tx,
                                messages,
                                settings
                                    .opened_store_id
                                    .as_ref()
                                    .map(|store_id| store_id.application_id()),
                                // We never want to patch blueprints' store IDs, only their app IDs.
                                None,
                            );
                        }
                    })
                    .with_context(|| format!("Failed to spawn IO thread for {filepath:?}"))?;
            }

            "dlr" => {
                let file = std::fs::File::open(&filepath)
                    .with_context(|| format!("Failed to open file {filepath:?}"))?;
                let file = std::io::BufReader::new(file);

                let messages = Decoder::decode_eager(file)?;

                // NOTE: This is IO bound, it must run on a dedicated thread, not the shared rayon thread pool.
                std::thread::Builder::new()
                    .name(format!("decode_and_stream({filepath:?})"))
                    .spawn({
                        let filepath = filepath.clone();
                        move || {
                            decode_and_stream(
                                &filepath, &tx, messages,
                                // Never use import semantics for .dlr files
                                None, None,
                            );
                        }
                    })
                    .with_context(|| format!("Failed to spawn IO thread for {filepath:?}"))?;
            }
            _ => unreachable!(),
        }

        Ok(())
    }

    fn import_from_file_contents(
        &self,
        settings: &crate::ImporterSettings,
        filepath: std::path::PathBuf,
        contents: std::borrow::Cow<'_, [u8]>,
        tx: crossbeam::channel::Sender<crate::ImportedData>,
    ) -> Result<(), crate::ImporterError> {
        dl_tracing::profile_function!(filepath.display().to_string());

        let extension = normalize_extension(&crate::extension(&filepath), &filepath);
        if !matches!(extension.as_str(), "dbl" | "dlr") {
            // NOTE: blueprints and recordings has the same file format
            return Err(crate::ImporterError::Incompatible(filepath));
        }

        let contents = std::io::Cursor::new(contents);
        let messages = match Decoder::decode_eager(contents) {
            Ok(decoder) => decoder,
            Err(err) => match err {
                // simply not interested
                dl_log_encoding::DecodeError::Codec(
                    dl_log_encoding::dlr::CodecError::NotAnRrd(_)
                    | dl_log_encoding::dlr::CodecError::InvalidOptions(_),
                ) => return Ok(()),
                _ => return Err(err.into()),
            },
        };

        // * We never want to patch blueprints' store IDs, only their app IDs.
        // * We never use import semantics at all for .dlr files.
        let forced_application_id = if extension == "dbl" {
            settings
                .opened_store_id
                .as_ref()
                .map(|store_id| store_id.application_id())
        } else {
            None
        };
        let forced_recording_id = None;

        decode_and_stream(
            &filepath,
            &tx,
            messages,
            forced_application_id,
            forced_recording_id,
        );

        Ok(())
    }
}

/// Maps legacy upstream Rerun extensions (`.rrd`, `.rbl`) onto their Dalaran equivalents.
///
/// The on-disk framing is identical (Dalaran deliberately kept the `RRF2` fourcc), so legacy files
/// are read natively without any conversion step. We only tell the user about it once, when the
/// file is picked up.
///
/// Anything that isn't a legacy extension is returned unchanged.
fn normalize_extension(extension: &str, filepath: &std::path::Path) -> String {
    if let Some(dalaran_extension) = crate::dalaran_extension_for_legacy(extension) {
        dl_log::info!(
            "Loaded legacy Rerun recording {} (.{extension}); Dalaran reads these natively.",
            filepath.display(),
        );
        dalaran_extension.to_owned()
    } else {
        extension.to_owned()
    }
}

#[test]
fn test_normalize_extension() {
    let path = std::path::Path::new("recording.rrd");
    assert_eq!(normalize_extension("rrd", path), "dlr");
    assert_eq!(normalize_extension("rbl", path), "dbl");
    assert_eq!(normalize_extension("dlr", path), "dlr");
    assert_eq!(normalize_extension("dbl", path), "dbl");
    assert_eq!(normalize_extension("mcap", path), "mcap");
}

fn decode_and_stream(
    filepath: &std::path::Path,
    tx: &crossbeam::channel::Sender<crate::ImportedData>,
    msgs: impl Iterator<Item = Result<dl_log_types::LogMsg, dl_log_encoding::DecodeError>>,
    forced_application_id: Option<&ApplicationId>,
    forced_recording_id: Option<&String>,
) {
    dl_tracing::profile_function!(filepath.display().to_string());

    for msg in msgs {
        let msg = match msg {
            Ok(msg) => msg,
            Err(err) => {
                dl_log::warn!(?filepath, "Failed to decode message: {err}");
                continue;
            }
        };

        let msg = if forced_application_id.is_some() || forced_recording_id.is_some() {
            match msg {
                dl_log_types::LogMsg::SetStoreInfo(set_store_info) => {
                    let mut store_id = set_store_info.info.store_id.clone();
                    if let Some(forced_application_id) = forced_application_id {
                        store_id = store_id.with_application_id(forced_application_id.clone());
                    }
                    if let Some(forced_recording_id) = forced_recording_id {
                        store_id = store_id.with_recording_id(forced_recording_id.clone());
                    }

                    dl_log_types::LogMsg::SetStoreInfo(dl_log_types::SetStoreInfo {
                        info: dl_log_types::StoreInfo {
                            store_id,
                            ..set_store_info.info
                        },
                        ..set_store_info
                    })
                }

                dl_log_types::LogMsg::ArrowMsg(mut store_id, arrow_msg) => {
                    if let Some(forced_application_id) = forced_application_id {
                        store_id = store_id.with_application_id(forced_application_id.clone());
                    }
                    if let Some(forced_recording_id) = forced_recording_id {
                        store_id = store_id.with_recording_id(forced_recording_id.clone());
                    }

                    dl_log_types::LogMsg::ArrowMsg(store_id, arrow_msg)
                }

                dl_log_types::LogMsg::BlueprintActivationCommand(blueprint_activation_command) => {
                    let mut blueprint_id = blueprint_activation_command.blueprint_id.clone();
                    if let Some(forced_application_id) = forced_application_id {
                        blueprint_id =
                            blueprint_id.with_application_id(forced_application_id.clone());
                    }
                    dl_log_types::LogMsg::BlueprintActivationCommand(
                        dl_log_types::BlueprintActivationCommand {
                            blueprint_id,
                            ..blueprint_activation_command
                        },
                    )
                }
            }
        } else {
            msg
        };

        let data = ImportedData::LogMsg(RrdImporter::name(&RrdImporter), msg);
        if dl_quota_channel::send_crossbeam(tx, data).is_err() {
            break; // The other end has decided to hang up, not our problem.
        }
    }
}
