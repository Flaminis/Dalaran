//! Recording integrity: is this `.dlr` file actually loadable?
//!
//! "The viewer will not open my recording" is usually one of three things: the file is not a
//! Dalaran recording at all (someone renamed an MCAP file), it was truncated because the process
//! died before the stream was flushed, or it is empty because nothing was ever logged. All three
//! look identical from the outside, so we decode the file and say which one it is.
//!
//! The decoding is done with `dl_log_encoding`, i.e. the very same code path the viewer uses, so
//! that a file this check accepts is a file the viewer can open.

use std::collections::BTreeSet;
use std::io::Read as _;
use std::path::Path;

use dl_log_types::LogMsg;
use serde_json::json;

use super::report::{Check, Status};

// ---

/// Extensions that upstream Rerun used, which Dalaran still reads natively.
const LEGACY_EXTENSIONS: &[&str] = &["rrd", "rbl"];

/// Decodes `path` and reports whether it is a recording the viewer can open.
pub fn check_recording(path: &Path) -> Check {
    let extension = path
        .extension()
        .and_then(|extension| extension.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase();
    let is_legacy = LEGACY_EXTENSIONS.contains(&extension.as_str());

    let check = Check::new("recording", Status::Ok, String::new())
        .with_detail("path", path.display().to_string())
        .with_detail("extension", format!(".{extension}"))
        .with_detail("legacy_rerun_file", is_legacy);

    let file = match std::fs::File::open(path) {
        Ok(file) => file,
        Err(err) => {
            return check
                .with_status(Status::Fail, format!("{}: {err}", path.display()))
                .with_detail("error", err.to_string());
        }
    };

    let size_bytes = file.metadata().map(|metadata| metadata.len()).unwrap_or(0);
    let check = check.with_detail("size_bytes", size_bytes);

    let mut reader = std::io::BufReader::new(file);

    // Read the framing header by hand first: a wrong fourcc deserves a much better message than
    // whatever the decoder would say about the bytes that follow it.
    let mut fourcc = [0u8; 4];
    if let Err(err) = reader.read_exact(&mut fourcc) {
        return check
            .with_status(
                Status::Fail,
                format!("{}: too small to be a recording", path.display()),
            )
            .with_detail("error", err.to_string())
            .with_hint("The file is truncated; only the first few bytes were ever written.");
    }

    let check = check.with_detail("fourcc", String::from_utf8_lossy(&fourcc).into_owned());

    if dl_log_encoding::OLD_DLR_FOURCC.contains(&fourcc) {
        return check
            .with_status(
                Status::Fail,
                format!(
                    "{}: written by a Dalaran/Rerun version that is too old",
                    path.display()
                ),
            )
            .with_hint(
                "Open it with the version that wrote it and re-save, or use `dalaran dlr migrate`.",
            );
    }

    if fourcc != dl_log_encoding::DLR_FOURCC {
        return check
            .with_status(
                Status::Fail,
                format!("{}: not a Dalaran recording", path.display()),
            )
            .with_hint(
                "Recordings start with the `RRF2` magic bytes. If this is an MCAP, URDF or other \
                 supported file, convert it first with `dalaran convert`.",
            );
    }

    // Rewind: the decoder wants to parse the header itself.
    let file = match std::fs::File::open(path) {
        Ok(file) => file,
        Err(err) => {
            return check
                .with_status(Status::Fail, format!("{}: {err}", path.display()))
                .with_detail("error", err.to_string());
        }
    };

    let decoder =
        match dl_log_encoding::Decoder::<LogMsg>::decode_eager(std::io::BufReader::new(file)) {
            Ok(decoder) => decoder,
            Err(err) => {
                return check
                    .with_status(
                        Status::Fail,
                        format!("{}: the stream header is corrupt", path.display()),
                    )
                    .with_detail("error", err.to_string())
                    .with_hint("The file was most likely truncated or partially overwritten.");
            }
        };

    let mut decoder = decoder;
    let mut num_messages = 0u64;
    let mut num_chunks = 0u64;
    let mut application_ids = BTreeSet::new();
    let mut store_ids = BTreeSet::new();
    let mut store_versions = BTreeSet::new();
    let mut decode_error = None;

    while let Some(message) = decoder.next() {
        match message {
            Ok(message) => {
                num_messages += 1;
                application_ids.insert(message.store_id().application_id().to_string());
                store_ids.insert(message.store_id().to_string());

                match message {
                    LogMsg::ArrowMsg(..) => num_chunks += 1,
                    LogMsg::SetStoreInfo(set_store_info) => {
                        if let Some(version) = set_store_info.info.store_version {
                            store_versions.insert(version.to_string());
                        }
                    }
                    LogMsg::BlueprintActivationCommand(..) => {}
                }
            }

            Err(err) => {
                // Keep what we decoded so far: "1200 messages then garbage" is a much more useful
                // diagnosis than "corrupt".
                decode_error = Some(err.to_string());
                break;
            }
        }
    }

    // A file that was closed properly ends in a footer. A recording whose producer was killed
    // decodes perfectly well right up to where it stops, so the missing footer is the only thing
    // that distinguishes "complete" from "we lost the tail".
    let num_footers = decoder.dlr_manifests().map(|manifests| manifests.len());

    let check = check
        .with_detail("num_footers", num_footers.as_ref().ok().copied())
        .with_detail("num_messages", num_messages)
        .with_detail("num_chunks", num_chunks)
        .with_detail("application_ids", json!(application_ids))
        .with_detail("store_ids", json!(store_ids))
        .with_detail("store_versions", json!(store_versions));

    if let Some(error) = decode_error {
        return check
            .with_status(
                Status::Fail,
                format!(
                    "{}: decoding failed after {num_messages} message(s)",
                    path.display()
                ),
            )
            .with_detail("error", error)
            .with_hint(
                "The recording was most likely truncated: the process died before the stream was \
                 flushed. Everything up to that point is still readable by the viewer.",
            );
    }

    if !matches!(num_footers, Ok(1..)) {
        return check
            .with_status(
                Status::Warn,
                format!(
                    "{}: {num_messages} message(s) decoded, but the stream has no footer",
                    path.display()
                ),
            )
            .with_hint(
                "The recording was never closed: the producer was most likely killed before the \
                 stream was flushed. The data that is there still loads, but the tail is gone.",
            );
    }

    if num_chunks == 0 {
        return check
            .with_status(
                Status::Warn,
                format!("{}: valid, but contains no data", path.display()),
            )
            .with_hint(
                "The stream is well-formed but nothing was ever logged into it. Check that your \
                 `log()` calls run before the recording stream is dropped.",
            );
    }

    let app_id = application_ids
        .iter()
        .next()
        .map_or("<unknown>", String::as_str);
    let legacy_note = if is_legacy {
        " (legacy Rerun file, read natively)"
    } else {
        ""
    };

    check.with_status(
        Status::Ok,
        format!(
            "{}: {num_messages} message(s), {num_chunks} chunk(s), app id {app_id}{legacy_note}",
            path.display()
        ),
    )
}

#[cfg(test)]
mod tests {
    use std::io::Write as _;

    use super::*;

    /// Writes a small but real recording, whatever extension `path` may have.
    fn write_recording(path: &Path) {
        let rec = crate::RecordingStreamBuilder::new("doctor_test")
            .save(path)
            .unwrap();
        for i in 0..4 {
            rec.set_time_sequence("frame", i);
            rec.log("points", &crate::Points2D::new([(1.0, 2.0), (3.0, 4.0)]))
                .unwrap();
        }
        drop(rec); // flushes
    }

    #[test]
    fn test_a_good_recording_passes() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("good.dlr");
        write_recording(&path);

        let check = check_recording(&path);
        assert_eq!(
            check.status,
            Status::Ok,
            "{} {:?}",
            check.summary,
            check.details
        );
        assert_eq!(check.details["fourcc"], "RRF2");
        assert_eq!(check.details["legacy_rerun_file"], false);
        assert_eq!(check.details["application_ids"], json!(["doctor_test"]));
        assert!(0 < check.details["num_chunks"].as_u64().unwrap());
        assert!(check.hint.is_none());
    }

    #[test]
    fn test_a_legacy_rrd_is_read_natively() {
        // A `.rrd` written by upstream Rerun is byte-identical to a `.dlr`, so this is a faithful
        // stand-in for one.
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("legacy.rrd");
        write_recording(&path);

        let check = check_recording(&path);
        assert_eq!(check.status, Status::Ok, "{}", check.summary);
        assert_eq!(check.details["legacy_rerun_file"], true);
        assert!(
            check.summary.contains("legacy Rerun file"),
            "{}",
            check.summary
        );
    }

    #[test]
    fn test_a_missing_file_fails() {
        let dir = tempfile::tempdir().unwrap();
        let check = check_recording(&dir.path().join("nope.dlr"));
        assert_eq!(check.status, Status::Fail);
        assert!(check.details["error"].is_string());
    }

    #[test]
    fn test_something_that_is_not_a_recording_fails() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("renamed.dlr");
        std::fs::write(&path, b"\x89PNG\r\n\x1a\n and then some").unwrap();

        let check = check_recording(&path);
        assert_eq!(check.status, Status::Fail);
        assert!(check.summary.contains("not a Dalaran recording"));
        assert!(check.hint.as_deref().unwrap().contains("dalaran convert"));
    }

    #[test]
    fn test_an_old_fourcc_is_named_as_such() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("ancient.dlr");
        std::fs::write(&path, b"RRF0\0\0\0\0\0\0\0\0").unwrap();

        let check = check_recording(&path);
        assert_eq!(check.status, Status::Fail);
        assert!(check.summary.contains("too old"), "{}", check.summary);
        assert_eq!(check.details["fourcc"], "RRF0");
    }

    #[test]
    fn test_an_empty_file_fails_cleanly() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("empty.dlr");
        std::fs::write(&path, b"").unwrap();

        let check = check_recording(&path);
        assert_eq!(check.status, Status::Fail);
        assert!(check.summary.contains("too small"));
        assert_eq!(check.details["size_bytes"], 0);
    }

    #[test]
    fn test_a_truncated_recording_reports_what_survived() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("truncated.dlr");
        write_recording(&path);

        let complete = check_recording(&path);
        assert_eq!(complete.status, Status::Ok, "{}", complete.summary);
        assert_eq!(complete.details["num_footers"], 1);

        // Chop off the tail, the way a process that died mid-flush would.
        let bytes = std::fs::read(&path).unwrap();
        let mut file = std::fs::File::create(&path).unwrap();
        file.write_all(&bytes[..bytes.len() * 2 / 3]).unwrap();
        drop(file);

        let check = check_recording(&path);
        assert_ne!(check.status, Status::Ok, "{}", check.summary);
        assert_eq!(check.details["fourcc"], "RRF2");
        assert!(check.hint.is_some());

        // Whatever survived must still be reported, rather than thrown away wholesale.
        let survived = check.details["num_messages"].as_u64().unwrap();
        assert!(0 < survived, "nothing was salvaged");
        assert!(survived <= complete.details["num_messages"].as_u64().unwrap());
        assert_eq!(check.details["num_footers"], 0);
    }
}
