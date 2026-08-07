use std::io::Write as _;
use std::path::{Path, PathBuf};

use anyhow::Context as _;
use dl_entity_db::EntityDb;
use dl_log_channel::{DataSourceMessage, SmartMessagePayload};
use dl_log_types::{ApplicationId, LogMsg, StoreId};
use dl_sdk::StoreKind;

// ---

/// Convert any supported file into a single Dalaran `.dlr` recording.
///
/// The same importers the Viewer uses are reused here, so anything that can be dragged into the
/// Viewer can be converted: MCAP (including ROS 2 and Foxglove messages), ROS bags exported to
/// MCAP, URDF robot descriptions, meshes, point clouds, images, video, Parquet, `LeRobot`
/// datasets, and of course Dalaran recordings themselves — including the legacy Rerun `.rrd`/`.rbl`
/// spelling.
///
/// Multiple inputs are merged into one output file. Recordings keep their own identity (store id)
/// unless `--app-id` is given, in which case every store is retargeted to that application.
///
/// Examples:
///
/// * Convert an MCAP file recorded on a robot:
///   `dalaran convert session.mcap -o session.dlr`
///
/// * Merge a robot description and a log into one recording:
///   `dalaran convert robot.urdf session.mcap -o session.dlr --app-id my_robot`
///
/// * Normalize a legacy Rerun recording (Dalaran can also read it as-is):
///   `dalaran convert legacy.rrd -o legacy.dlr`
///
/// * List everything this build can ingest:
///   `dalaran convert --list-formats`
#[derive(Debug, Clone, clap::Parser)]
pub struct ConvertCommand {
    /// The files (or directories) to convert.
    ///
    /// Directories are traversed recursively, like they are in the Viewer.
    #[arg(value_name = "INPUT")]
    inputs: Vec<PathBuf>,

    /// Where to write the resulting recording.
    ///
    /// Required unless `--list-formats` is passed.
    #[arg(short = 'o', long = "output", value_name = "OUTPUT.dlr")]
    output: Option<PathBuf>,

    /// Force the application id of every converted store.
    ///
    /// By default each importer picks one, usually derived from the input file name.
    #[arg(long = "app-id", value_name = "ID")]
    app_id: Option<String>,

    /// Overwrite the output file if it already exists.
    #[arg(long)]
    overwrite: bool,

    /// Print every file extension this build can ingest, then exit.
    #[arg(long)]
    list_formats: bool,
}

impl ConvertCommand {
    pub fn run(&self) -> anyhow::Result<()> {
        if self.list_formats {
            print_supported_formats();
            return Ok(());
        }

        anyhow::ensure!(
            !self.inputs.is_empty(),
            "no inputs given; pass one or more files, or `--list-formats` to see what is supported"
        );

        let output = self.output.as_ref().context(
            "no output given; pass `-o <OUTPUT.dlr>` (or `--list-formats` to see what is supported)",
        )?;

        if output.exists() && !self.overwrite {
            anyhow::bail!("{output:?} already exists; pass `--overwrite` to replace it");
        }

        let output_extension = output
            .extension()
            .and_then(|extension| extension.to_str())
            .unwrap_or_default()
            .to_ascii_lowercase();
        if !matches!(output_extension.as_str(), "dlr" | "dbl") {
            dl_log::warn!(
                "Output {output:?} does not end in `.dlr`; it will still be written as a Dalaran recording."
            );
        }

        let application_id = self
            .app_id
            .as_deref()
            .map(ApplicationId::try_new)
            .transpose()
            .context("invalid `--app-id`")?;

        let mut entity_dbs: std::collections::BTreeMap<StoreId, EntityDb> = Default::default();

        for input in &self.inputs {
            import_into(input, application_id.as_ref(), &mut entity_dbs)
                .with_context(|| format!("failed to convert {input:?}"))?;
        }

        anyhow::ensure!(
            !entity_dbs.is_empty(),
            "the inputs did not produce any data; nothing to write"
        );

        write_dlr(output, &entity_dbs)
    }
}

/// Runs every importer over `path` and indexes the resulting messages into `entity_dbs`.
fn import_into(
    path: &Path,
    application_id: Option<&ApplicationId>,
    entity_dbs: &mut std::collections::BTreeMap<StoreId, EntityDb>,
) -> anyhow::Result<()> {
    anyhow::ensure!(path.exists(), "{path:?} does not exist");

    let (tx, rx) = dl_log_channel::log_channel(dl_log_channel::LogSource::File {
        path: path.to_owned(),
    });

    let settings = dl_importer::ImporterSettings {
        application_id: application_id.cloned(),
        ..dl_importer::ImporterSettings::recommended(dl_log_types::RecordingId::random())
    };

    dl_importer::import_from_path(&settings, dl_log_types::FileSource::Cli, path, &tx)?;

    // The importers keep their own clones of the sender alive for as long as they have work to do;
    // ours would otherwise keep the channel open forever.
    drop(tx);

    let mut num_messages = 0u64;

    while let Ok(msg) = rx.recv() {
        match msg.payload {
            SmartMessagePayload::Msg(DataSourceMessage::LogMsg(msg)) => {
                let msg = retarget_application_id(msg, application_id);
                let store_id = msg.store_id().clone();
                let db = entity_dbs.entry(store_id.clone()).or_insert_with(|| {
                    // Headless conversion: viewer indexes would only slow us down, and we do not
                    // want to re-chunk the data differently than it was given to us.
                    let enable_viewer_indexes = false;
                    EntityDb::with_store_config(
                        store_id,
                        enable_viewer_indexes,
                        dl_chunk_store::ChunkStoreConfig::ALL_DISABLED,
                    )
                });
                db.add_log_msg(&msg)?;
                num_messages += 1;
            }

            SmartMessagePayload::Msg(
                DataSourceMessage::RrdManifest(..) | DataSourceMessage::RrdManifestComplete(..),
            ) => {
                // Manifests are an index over data we are about to receive in full anyway,
                // and they are regenerated on encode.
            }

            SmartMessagePayload::Msg(DataSourceMessage::TableMsg(_)) => {
                anyhow::bail!("tables cannot be stored in a recording");
            }

            SmartMessagePayload::Msg(DataSourceMessage::UiCommand(command)) => {
                dl_log::debug!("ignoring UI command while converting: {command:?}");
            }

            SmartMessagePayload::Flush { on_flush_done } => on_flush_done(),

            SmartMessagePayload::Quit(err) => {
                if let Some(err) = err {
                    return Err(anyhow::anyhow!("{err}"))
                        .with_context(|| format!("importer failed on {path:?}"));
                }
                break;
            }
        }
    }

    anyhow::ensure!(0 < num_messages, "{path:?} did not contain any data");

    dl_log::info!("Converted {path:?} ({num_messages} messages)");

    Ok(())
}

/// Rewrites the application id of a message, if one was forced on the command line.
fn retarget_application_id(msg: LogMsg, application_id: Option<&ApplicationId>) -> LogMsg {
    let Some(application_id) = application_id else {
        return msg;
    };

    match msg {
        LogMsg::SetStoreInfo(set_store_info) => LogMsg::SetStoreInfo(dl_log_types::SetStoreInfo {
            info: dl_log_types::StoreInfo {
                store_id: set_store_info
                    .info
                    .store_id
                    .with_application_id(application_id.clone()),
                ..set_store_info.info
            },
            ..set_store_info
        }),

        LogMsg::ArrowMsg(store_id, arrow_msg) => LogMsg::ArrowMsg(
            store_id.with_application_id(application_id.clone()),
            arrow_msg,
        ),

        LogMsg::BlueprintActivationCommand(command) => {
            LogMsg::BlueprintActivationCommand(dl_log_types::BlueprintActivationCommand {
                blueprint_id: command
                    .blueprint_id
                    .with_application_id(application_id.clone()),
                ..command
            })
        }
    }
}

/// Encodes every store into a single `.dlr` file at `output`.
fn write_dlr(
    output: &Path,
    entity_dbs: &std::collections::BTreeMap<StoreId, EntityDb>,
) -> anyhow::Result<()> {
    if let Some(parent) = output.parent()
        && !parent.as_os_str().is_empty()
    {
        std::fs::create_dir_all(parent)
            .with_context(|| format!("couldn't create output directory {parent:?}"))?;
    }

    let mut file = std::io::BufWriter::new(
        std::fs::File::create(output).with_context(|| format!("couldn't create {output:?}"))?,
    );

    // Blueprints must come first so that the Viewer can set up the viewport before the data
    // starts flowing in.
    let messages_dbl = entity_dbs
        .values()
        .filter(|db| db.store_kind() == StoreKind::Blueprint)
        .flat_map(|db| db.to_messages(None /* time selection */));
    let messages_dlr = entity_dbs
        .values()
        .filter(|db| db.store_kind() == StoreKind::Recording)
        .flat_map(|db| db.to_messages(None /* time selection */));

    let version = entity_dbs
        .values()
        .next()
        .and_then(|db| db.store_info())
        .and_then(|info| info.store_version)
        .unwrap_or(dl_build_info::CrateVersion::LOCAL);

    let size_bytes = dl_log_encoding::Encoder::encode_into(
        version,
        dl_log_encoding::dlr::EncodingOptions::PROTOBUF_COMPRESSED,
        std::iter::chain(messages_dbl, messages_dlr),
        &mut file,
    )
    .context("couldn't encode messages")?;

    file.flush().context("couldn't flush output")?;
    drop(file);

    // `encode_into` reports the encoded payload size, which excludes framing; report what the
    // user will actually see on disk instead.
    let size_on_disk = std::fs::metadata(output)
        .map(|metadata| metadata.len())
        .unwrap_or(size_bytes);

    dl_log::info!(
        "Wrote {} to {output:?} ({} store(s))",
        dl_format::format_bytes(size_on_disk as _),
        entity_dbs.len(),
    );

    Ok(())
}

/// Prints every extension the builtin importers understand, grouped by kind.
fn print_supported_formats() {
    let groups: [(&str, &[&str]); 9] = [
        (
            "Dalaran recordings",
            dl_importer::SUPPORTED_DALARAN_EXTENSIONS,
        ),
        (
            "Legacy Rerun recordings (read natively)",
            dl_importer::LEGACY_RERUN_EXTENSIONS,
        ),
        (
            "Third-party formats",
            dl_importer::SUPPORTED_THIRD_PARTY_FORMATS,
        ),
        ("Images", dl_importer::SUPPORTED_IMAGE_EXTENSIONS),
        (
            "Depth images",
            dl_importer::SUPPORTED_DEPTH_IMAGE_EXTENSIONS,
        ),
        ("Video", dl_importer::SUPPORTED_VIDEO_EXTENSIONS),
        ("3D models", dl_importer::SUPPORTED_MESH_EXTENSIONS),
        (
            "Point clouds",
            dl_importer::SUPPORTED_POINT_CLOUD_EXTENSIONS,
        ),
        ("Tabular data", dl_importer::SUPPORTED_PARQUET_EXTENSIONS),
    ];

    for (label, extensions) in groups {
        let extensions = extensions
            .iter()
            .map(|extension| format!(".{extension}"))
            .collect::<Vec<_>>()
            .join(" ");
        println!("{label}: {extensions}");
    }

    let text = dl_importer::SUPPORTED_TEXT_EXTENSIONS
        .iter()
        .map(|extension| format!(".{extension}"))
        .collect::<Vec<_>>()
        .join(" ");
    println!("Text: {text}");
    println!();
    println!(
        "Additional formats can be added through external importers on $PATH; \
         see https://www.dalaran.dev/docs/concepts/logging-and-ingestion/importers/overview"
    );
}

#[cfg(test)]
mod tests {
    use clap::Parser as _;

    use super::*;

    #[derive(Debug, clap::Parser)]
    struct Wrapper {
        #[command(subcommand)]
        command: Sub,
    }

    #[derive(Debug, clap::Subcommand)]
    enum Sub {
        Convert(ConvertCommand),
    }

    fn parse(args: &[&str]) -> ConvertCommand {
        let Sub::Convert(cmd) = Wrapper::parse_from(args).command;
        cmd
    }

    #[test]
    fn test_parses_inputs_and_flags() {
        let cmd = parse(&[
            "dalaran",
            "convert",
            "a.mcap",
            "b.rrd",
            "-o",
            "out.dlr",
            "--app-id",
            "my_robot",
            "--overwrite",
        ]);

        assert_eq!(
            cmd.inputs,
            vec![PathBuf::from("a.mcap"), PathBuf::from("b.rrd")]
        );
        assert_eq!(cmd.output, Some(PathBuf::from("out.dlr")));
        assert_eq!(cmd.app_id.as_deref(), Some("my_robot"));
        assert!(cmd.overwrite);
        assert!(!cmd.list_formats);
    }

    #[test]
    fn test_list_formats_needs_no_input() {
        let cmd = parse(&["dalaran", "convert", "--list-formats"]);
        assert!(cmd.list_formats);
        assert!(cmd.inputs.is_empty());
        // Must not fail just because there is no input/output.
        cmd.run().unwrap();
    }

    #[test]
    fn test_missing_output_is_an_error() {
        let err = parse(&["dalaran", "convert", "a.mcap"])
            .run()
            .unwrap_err()
            .to_string();
        assert!(err.contains("-o"), "unexpected error: {err}");
    }

    #[test]
    fn test_refuses_to_clobber_without_overwrite() {
        let existing = tempfile::NamedTempFile::new().unwrap();
        let output = existing.path().to_string_lossy().to_string();

        let err = parse(&["dalaran", "convert", "a.mcap", "-o", &output])
            .run()
            .unwrap_err()
            .to_string();
        assert!(err.contains("--overwrite"), "unexpected error: {err}");
    }

    /// Writes a small recording to `path`, whatever extension it may have.
    fn write_recording(path: &Path) {
        let rec = crate::RecordingStreamBuilder::new("convert_test")
            .save(path)
            .unwrap();
        for i in 0..4 {
            rec.set_time_sequence("frame", i);
            rec.log(
                "points",
                &crate::Points2D::new([(1.0, 2.0), (3.0, 4.0)]).with_radii([1.0]),
            )
            .unwrap();
        }
        drop(rec); // flushes
    }

    /// Counts the messages in a recording, and asserts it uses the expected framing.
    fn read_back(path: &Path) -> usize {
        let bytes = std::fs::read(path).unwrap();
        assert!(
            bytes.starts_with(b"RRF2"),
            "{path:?} is not a Dalaran recording"
        );

        dl_log_encoding::Decoder::decode_eager(std::io::Cursor::new(bytes))
            .unwrap()
            .map(Result::unwrap)
            .filter(|msg| matches!(msg, LogMsg::ArrowMsg(..)))
            .count()
    }

    #[test]
    fn test_round_trips_a_legacy_rerun_recording() {
        // A `.rrd` is byte-identical to a `.dlr`, so writing one and renaming it is a faithful
        // stand-in for a recording produced by upstream Rerun.
        let dir = tempfile::tempdir().unwrap();
        let legacy = dir.path().join("legacy.rrd");
        write_recording(&legacy);
        let num_messages = read_back(&legacy);
        assert!(0 < num_messages);

        let output = dir.path().join("converted.dlr");
        parse(&[
            "dalaran",
            "convert",
            legacy.to_str().unwrap(),
            "-o",
            output.to_str().unwrap(),
            "--app-id",
            "converted_app",
        ])
        .run()
        .unwrap();

        assert_eq!(read_back(&output), num_messages);

        // Converting again must refuse to clobber, but succeed with `--overwrite`.
        let args = [
            "dalaran",
            "convert",
            legacy.to_str().unwrap(),
            "-o",
            output.to_str().unwrap(),
        ];
        assert!(parse(&args).run().is_err());
        parse(&[args.as_slice(), &["--overwrite"]].concat())
            .run()
            .unwrap();
    }

    #[test]
    fn test_merges_several_inputs_into_one_recording() {
        let dir = tempfile::tempdir().unwrap();

        let first = dir.path().join("first.dlr");
        let second = dir.path().join("second.rrd");
        write_recording(&first);
        write_recording(&second);

        let output = dir.path().join("merged.dlr");
        parse(&[
            "dalaran",
            "convert",
            first.to_str().unwrap(),
            second.to_str().unwrap(),
            "-o",
            output.to_str().unwrap(),
        ])
        .run()
        .unwrap();

        assert_eq!(read_back(&output), read_back(&first) + read_back(&second));
    }

    #[test]
    fn test_missing_input_is_an_error() {
        let dir = tempfile::tempdir().unwrap();
        let output = dir.path().join("out.dlr");

        let err = parse(&[
            "dalaran",
            "convert",
            "does_not_exist.mcap",
            "-o",
            output.to_str().unwrap(),
        ])
        .run()
        .unwrap_err()
        .to_string();
        assert!(err.contains("does_not_exist.mcap"), "unexpected: {err}");
        assert!(!output.exists(), "no output should have been written");
    }

    #[test]
    fn test_every_supported_extension_is_listed() {
        // `--list-formats` must not silently drift away from what we actually accept.
        let listed: std::collections::BTreeSet<_> = [
            dl_importer::SUPPORTED_DALARAN_EXTENSIONS,
            dl_importer::LEGACY_RERUN_EXTENSIONS,
            dl_importer::SUPPORTED_THIRD_PARTY_FORMATS,
            dl_importer::SUPPORTED_IMAGE_EXTENSIONS,
            dl_importer::SUPPORTED_DEPTH_IMAGE_EXTENSIONS,
            dl_importer::SUPPORTED_VIDEO_EXTENSIONS,
            dl_importer::SUPPORTED_MESH_EXTENSIONS,
            dl_importer::SUPPORTED_POINT_CLOUD_EXTENSIONS,
            dl_importer::SUPPORTED_PARQUET_EXTENSIONS,
            dl_importer::SUPPORTED_TEXT_EXTENSIONS,
        ]
        .into_iter()
        .flatten()
        .copied()
        .collect();

        let supported: std::collections::BTreeSet<_> =
            dl_importer::supported_extensions().collect();

        assert_eq!(listed, supported);
    }
}
