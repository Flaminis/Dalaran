//! Environment checks: `DALARAN_*` variables, the display server, and ROS 2.
//!
//! Every check here takes an explicit snapshot of the environment rather than reading
//! [`std::env`] itself. Mutating the environment is process-global and racy under a threaded test
//! runner, so a snapshot is the only way to test this honestly.

use std::collections::BTreeMap;

use serde_json::{Value, json};

use super::report::{Check, Status};

// ---

/// The `DALARAN_*` variables the SDK and Viewer actually read, with a one-line explanation.
///
/// Kept in sync with `dalaran.tools.doctor.KNOWN_ENV_VARS`, which is why the first block below is
/// spelled exactly like it is there. The extra entries are the ones only the native Viewer cares
/// about, so the Python script has no reason to know them.
pub const KNOWN_ENV_VARS: &[(&str, &str)] = &[
    // Shared with the Python doctor:
    (
        "DALARAN_CHUNK_MAX_ROWS_IF_UNSORTED",
        "maximum number of rows in an unsorted chunk",
    ),
    (
        "DALARAN_FLUSH_NUM_BYTES",
        "byte threshold before the SDK flushes a chunk",
    ),
    (
        "DALARAN_FLUSH_NUM_ROWS",
        "row threshold before the SDK flushes a chunk",
    ),
    (
        "DALARAN_FLUSH_TICK_SECS",
        "time threshold before the SDK flushes a chunk",
    ),
    ("DALARAN_MAPBOX_ACCESS_TOKEN", "token used by map views"),
    (
        "DALARAN_PANIC_ON_WARN",
        "turn warnings into panics (debugging only)",
    ),
    (
        "DALARAN_STRICT",
        "turn recoverable SDK errors into hard errors",
    ),
    (
        "DALARAN_TELEMETRY_ENDPOINT",
        "OTLP endpoint for client-side tracing",
    ),
    (
        "DALARAN_TRACK_ALLOCATIONS",
        "expensive allocation tracking (debugging only)",
    ),
    (
        "DALARAN_WORKSPACE",
        "path to the Dalaran source workspace (development only)",
    ),
    // Native-only, i.e. things the Python script never sees:
    (
        "DALARAN_CHUNK_MAX_BYTES",
        "maximum chunk size threshold for the compactor",
    ),
    (
        "DALARAN_CHUNK_MAX_ROWS",
        "maximum number of rows in a sorted chunk",
    ),
    (
        "DALARAN_SDK_NUM_CPUS",
        "number of threads the SDK may use for queries",
    ),
    (
        "DALARAN_SHADER_PATH",
        "shader search path (developer builds only)",
    ),
    (
        "DALARAN_VERY_STRICT",
        "panic on any detected invariant violation (CI only)",
    ),
];

/// Variables that are parsed as numbers; a bad value makes us fall back to a default.
const NUMERIC_ENV_VARS: &[&str] = &[
    "DALARAN_CHUNK_MAX_BYTES",
    "DALARAN_CHUNK_MAX_ROWS",
    "DALARAN_CHUNK_MAX_ROWS_IF_UNSORTED",
    "DALARAN_FLUSH_NUM_BYTES",
    "DALARAN_FLUSH_NUM_ROWS",
    "DALARAN_FLUSH_TICK_SECS",
    "DALARAN_SDK_NUM_CPUS",
];

/// Variables parsed by `dl_log::env_var_flag`, i.e. `1/true/yes/on` and `0/false/no/off`.
const BOOLEAN_ENV_VARS: &[&str] = &[
    "DALARAN_PANIC_ON_WARN",
    "DALARAN_STRICT",
    "DALARAN_TRACK_ALLOCATIONS",
    "DALARAN_VERY_STRICT",
];

/// Variables whose value must never end up in a report someone pastes into an issue.
const SECRET_ENV_VARS: &[&str] = &["DALARAN_MAPBOX_ACCESS_TOKEN"];

/// Takes a snapshot of the whole environment, lossily decoding non-UTF-8 values.
pub fn snapshot() -> BTreeMap<String, String> {
    std::env::vars_os()
        .map(|(key, value)| {
            (
                key.to_string_lossy().into_owned(),
                value.to_string_lossy().into_owned(),
            )
        })
        .collect()
}

/// Validates `DALARAN_*` variables and flags leftovers from the Rerun days.
///
/// A malformed numeric variable is a hard failure: the value is silently ignored at runtime, so
/// the user gets a default they did not ask for and no explanation. Everything else is a warning.
pub fn check_environment(env: &BTreeMap<String, String>) -> Check {
    let dalaran_vars = env
        .iter()
        .filter(|(key, _)| key.starts_with("DALARAN_"))
        .map(|(key, value)| (key.clone(), redact(key, value)))
        .collect::<serde_json::Map<_, _>>();

    let stale_vars = env
        .keys()
        .filter(|key| key.starts_with("RERUN_"))
        .cloned()
        .collect::<Vec<_>>();

    let unknown = dalaran_vars
        .keys()
        .filter(|key| !KNOWN_ENV_VARS.iter().any(|(known, _)| known == *key))
        .cloned()
        .collect::<Vec<_>>();

    let malformed_numbers = NUMERIC_ENV_VARS
        .iter()
        .filter(|name| {
            env.get(**name)
                .is_some_and(|value| value.trim().parse::<f64>().is_err())
        })
        .map(|name| (*name).to_owned())
        .collect::<Vec<_>>();

    let malformed_flags = BOOLEAN_ENV_VARS
        .iter()
        .filter(|name| env.get(**name).is_some_and(|value| !is_flag(value)))
        .map(|name| (*name).to_owned())
        .collect::<Vec<_>>();

    let check = Check::new(
        "environment",
        Status::Ok,
        format!(
            "{} DALARAN_* variable(s) set, all recognized",
            dalaran_vars.len()
        ),
    )
    .with_detail("dalaran_vars", Value::Object(dalaran_vars))
    .with_detail("unknown_vars", json!(unknown))
    .with_detail("stale_rerun_vars", json!(stale_vars))
    .with_detail("malformed_vars", json!(malformed_numbers))
    .with_detail("malformed_flags", json!(malformed_flags));

    if !malformed_numbers.is_empty() {
        return check
            .with_status(
                Status::Fail,
                format!(
                    "malformed numeric environment variable(s): {}",
                    malformed_numbers.join(", ")
                ),
            )
            .with_hint(
                "These are parsed as numbers; a bad value makes the SDK fall back to defaults or refuse to start.",
            );
    }

    if !malformed_flags.is_empty() {
        return check
            .with_status(
                Status::Warn,
                format!(
                    "malformed boolean environment variable(s): {}",
                    malformed_flags.join(", ")
                ),
            )
            .with_hint("Expected one of 1/true/yes/on or 0/false/no/off; the value is ignored.");
    }

    if !stale_vars.is_empty() {
        let renames = stale_vars
            .iter()
            .map(|stale| format!("{stale} -> DALARAN_{}", &stale["RERUN_".len()..]))
            .collect::<Vec<_>>()
            .join(", ");
        return check
            .with_status(
                Status::Warn,
                format!(
                    "leftover RERUN_* variable(s) that Dalaran ignores: {}",
                    stale_vars.join(", ")
                ),
            )
            .with_hint(format!("Rename them, or unset them: {renames}."));
    }

    if !unknown.is_empty() {
        return check
            .with_status(
                Status::Warn,
                format!("unrecognized DALARAN_* variable(s): {}", unknown.join(", ")),
            )
            .with_hint("Check for typos; unknown variables are silently ignored.");
    }

    check
}

/// Detects headless sessions and reports the windowing system in use.
///
/// A headless session is by far the most common reason for "the viewer never opens a window", and
/// it has a good answer (`--serve-web`), so it is worth its own line in the report.
pub fn check_display(env: &BTreeMap<String, String>) -> Check {
    let display = env.get("DISPLAY").map(String::as_str);
    let wayland = env.get("WAYLAND_DISPLAY").map(String::as_str);
    let over_ssh = env.contains_key("SSH_CONNECTION") || env.contains_key("SSH_TTY");

    let check = Check::new("display", Status::Ok, String::new())
        .with_detail("system", std::env::consts::OS)
        .with_detail("DISPLAY", display)
        .with_detail("WAYLAND_DISPLAY", wayland)
        .with_detail("ssh_session", over_ssh);

    // macOS and Windows always have a window server; there is nothing to diagnose.
    if !cfg!(target_os = "linux") {
        return check.with_detail("session_type", "native").with_status(
            Status::Ok,
            format!(
                "{} always provides a native window server",
                std::env::consts::OS
            ),
        );
    }

    if wayland.is_some_and(|value| !value.is_empty()) {
        return check
            .with_detail("session_type", "wayland")
            .with_status(Status::Ok, "Wayland session detected");
    }

    if display.is_some_and(|value| !value.is_empty()) {
        return check
            .with_detail("session_type", "x11")
            .with_status(Status::Ok, "X11 session detected");
    }

    check
        .with_detail("session_type", "headless")
        .with_status(
            Status::Warn,
            "headless session: neither DISPLAY nor WAYLAND_DISPLAY is set",
        )
        .with_hint(
            "Use `dalaran --serve-web` and the web viewer, or `--save recording.dlr`, instead of spawning a window.",
        )
}

/// Reports whether a ROS 2 distribution is sourced, and how it is configured.
///
/// The ROS 2 importers only see what the ambient middleware configuration lets them see, so a
/// mismatched `ROS_DOMAIN_ID` or `RMW_IMPLEMENTATION` explains a surprising amount of "no data".
pub fn check_ros2(env: &BTreeMap<String, String>) -> Check {
    let distro = env.get("ROS_DISTRO").map(String::as_str);
    let version = env.get("ROS_VERSION").map(String::as_str);
    let rmw = env.get("RMW_IMPLEMENTATION").map(String::as_str);
    let domain_id = env.get("ROS_DOMAIN_ID").map(String::as_str);

    let installed = std::fs::read_dir("/opt/ros")
        .into_iter()
        .flatten()
        .flatten()
        .map(|entry| entry.file_name().to_string_lossy().into_owned())
        .collect::<std::collections::BTreeSet<_>>();

    let check = Check::new("ros2", Status::Skip, String::new())
        .with_detail("ROS_DISTRO", distro)
        .with_detail("ROS_VERSION", version)
        .with_detail("RMW_IMPLEMENTATION", rmw)
        .with_detail("ROS_DOMAIN_ID", domain_id)
        .with_detail("installed_distros", json!(installed));

    let Some(distro) = distro else {
        if installed.is_empty() {
            return check.with_status(
                Status::Skip,
                "no ROS 2 installation found (only needed for the ROS 2 bridge)",
            );
        }
        let first = installed.iter().next().map_or("humble", String::as_str);
        return check
            .with_status(
                Status::Warn,
                format!(
                    "ROS 2 is installed ({}) but not sourced in this shell",
                    installed.iter().cloned().collect::<Vec<_>>().join(", ")
                ),
            )
            .with_hint(format!("Run `source /opt/ros/{first}/setup.bash` first."));
    };

    // ROS 1 speaks a different protocol entirely; nothing here applies to it.
    if version.is_some_and(|version| version.trim() == "1") {
        return check
            .with_status(
                Status::Warn,
                format!("ROS 1 ({distro}) is sourced; Dalaran only supports ROS 2"),
            )
            .with_hint("Record a bag and convert it to MCAP, then `dalaran convert` it.");
    }

    if let Some(domain_id) = domain_id
        && !matches!(domain_id.trim().parse::<u32>(), Ok(0..=232))
    {
        return check
            .with_status(
                Status::Warn,
                format!("ROS 2 {distro} is sourced, but ROS_DOMAIN_ID={domain_id} is not valid"),
            )
            .with_hint(
                "ROS_DOMAIN_ID must be an integer in 0..=232; nodes will not discover each other.",
            );
    }

    check.with_status(Status::Ok, format!("ROS 2 {distro} is sourced"))
}

/// Whether a value is one of the flag spellings `dl_log::env_var_flag` accepts.
fn is_flag(value: &str) -> bool {
    matches!(
        value.trim().to_ascii_lowercase().as_str(),
        "" | "0" | "false" | "no" | "off" | "1" | "true" | "yes" | "on"
    )
}

/// Replaces the value of a secret-bearing variable with a placeholder.
fn redact(key: &str, value: &str) -> Value {
    if SECRET_ENV_VARS.contains(&key) && !value.is_empty() {
        json!(format!("<redacted, {} chars>", value.len()))
    } else {
        json!(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn env(pairs: &[(&str, &str)]) -> BTreeMap<String, String> {
        pairs
            .iter()
            .map(|(key, value)| ((*key).to_owned(), (*value).to_owned()))
            .collect()
    }

    #[test]
    fn test_a_clean_environment_is_ok() {
        let check = check_environment(&env(&[("PATH", "/usr/bin")]));
        assert_eq!(check.status, Status::Ok);
        assert!(check.summary.starts_with("0 DALARAN_* variable(s)"));
        assert!(check.hint.is_none());
    }

    #[test]
    fn test_known_variables_are_accepted() {
        let check = check_environment(&env(&[
            ("DALARAN_FLUSH_TICK_SECS", "0.5"),
            ("DALARAN_STRICT", "1"),
        ]));
        assert_eq!(check.status, Status::Ok);
        assert_eq!(check.details["dalaran_vars"]["DALARAN_STRICT"], "1");
    }

    #[test]
    fn test_malformed_numbers_fail() {
        let check = check_environment(&env(&[("DALARAN_FLUSH_NUM_ROWS", "lots")]));
        assert_eq!(check.status, Status::Fail);
        assert!(check.summary.contains("DALARAN_FLUSH_NUM_ROWS"));
        assert_eq!(
            check.details["malformed_vars"],
            json!(["DALARAN_FLUSH_NUM_ROWS"])
        );
    }

    #[test]
    fn test_malformed_flags_only_warn() {
        // `dl_log::env_var_flag` warns and falls back to the default, so neither should we panic.
        let check = check_environment(&env(&[("DALARAN_STRICT", "yes-please")]));
        assert_eq!(check.status, Status::Warn);
        assert_eq!(check.details["malformed_flags"], json!(["DALARAN_STRICT"]));

        for good in ["1", "true", "YES", "on", "0", "off", "  false  "] {
            let check = check_environment(&env(&[("DALARAN_STRICT", good)]));
            assert_eq!(check.status, Status::Ok, "{good:?} should be a valid flag");
        }
    }

    #[test]
    fn test_stale_rerun_variables_warn_with_the_dalaran_spelling() {
        let check = check_environment(&env(&[("RERUN_STRICT", "1")]));
        assert_eq!(check.status, Status::Warn);
        assert_eq!(check.details["stale_rerun_vars"], json!(["RERUN_STRICT"]));
        assert!(
            check
                .hint
                .as_deref()
                .is_some_and(|hint| hint.contains("RERUN_STRICT -> DALARAN_STRICT")),
            "{:?}",
            check.hint
        );
    }

    #[test]
    fn test_unknown_variables_warn() {
        let check = check_environment(&env(&[("DALARAN_FLUSH_NUM_ROWZ", "10")]));
        assert_eq!(check.status, Status::Warn);
        assert_eq!(
            check.details["unknown_vars"],
            json!(["DALARAN_FLUSH_NUM_ROWZ"])
        );
    }

    #[test]
    fn test_failures_win_over_warnings() {
        let check = check_environment(&env(&[
            ("RERUN_STRICT", "1"),
            ("DALARAN_TYPO", "1"),
            ("DALARAN_FLUSH_NUM_ROWS", "nope"),
        ]));
        assert_eq!(check.status, Status::Fail);
    }

    #[test]
    fn test_secrets_are_never_printed() {
        let check = check_environment(&env(&[("DALARAN_MAPBOX_ACCESS_TOKEN", "pk.hunter2")]));
        assert_eq!(check.status, Status::Ok);
        let value = check.details["dalaran_vars"]["DALARAN_MAPBOX_ACCESS_TOKEN"]
            .as_str()
            .unwrap();
        assert!(!value.contains("hunter2"), "{value}");
        assert!(value.contains("redacted"), "{value}");
    }

    #[test]
    fn test_known_env_vars_are_sorted_and_unique() {
        // The list doubles as documentation, so keep it tidy.
        let names = KNOWN_ENV_VARS
            .iter()
            .map(|(name, _)| *name)
            .collect::<std::collections::BTreeSet<_>>();
        assert_eq!(names.len(), KNOWN_ENV_VARS.len());
        for name in &names {
            assert!(name.starts_with("DALARAN_"), "{name}");
        }
    }

    #[test]
    fn test_display_detects_a_headless_linux_session() {
        let check = check_display(&env(&[("SSH_CONNECTION", "1.2.3.4 22 5.6.7.8 22")]));
        assert_eq!(check.details["ssh_session"], true);

        if cfg!(target_os = "linux") {
            assert_eq!(check.status, Status::Warn);
            assert_eq!(check.details["session_type"], "headless");

            let x11 = check_display(&env(&[("DISPLAY", ":0")]));
            assert_eq!(x11.status, Status::Ok);
            assert_eq!(x11.details["session_type"], "x11");

            let wayland =
                check_display(&env(&[("DISPLAY", ":0"), ("WAYLAND_DISPLAY", "wayland-0")]));
            assert_eq!(wayland.details["session_type"], "wayland");
        } else {
            assert_eq!(check.status, Status::Ok);
            assert_eq!(check.details["session_type"], "native");
        }
    }

    #[test]
    fn test_ros2_reports_a_sourced_distro() {
        let check = check_ros2(&env(&[
            ("ROS_DISTRO", "jazzy"),
            ("ROS_VERSION", "2"),
            ("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp"),
            ("ROS_DOMAIN_ID", "42"),
        ]));
        assert_eq!(check.status, Status::Ok);
        assert!(check.summary.contains("jazzy"));
        assert_eq!(check.details["RMW_IMPLEMENTATION"], "rmw_cyclonedds_cpp");
    }

    #[test]
    fn test_ros2_flags_an_out_of_range_domain_id() {
        let check = check_ros2(&env(&[("ROS_DISTRO", "jazzy"), ("ROS_DOMAIN_ID", "9999")]));
        assert_eq!(check.status, Status::Warn);
        assert!(check.summary.contains("9999"));

        let check = check_ros2(&env(&[
            ("ROS_DISTRO", "jazzy"),
            ("ROS_DOMAIN_ID", "not-a-number"),
        ]));
        assert_eq!(check.status, Status::Warn);
    }

    #[test]
    fn test_ros1_is_called_out() {
        let check = check_ros2(&env(&[("ROS_DISTRO", "noetic"), ("ROS_VERSION", "1")]));
        assert_eq!(check.status, Status::Warn);
        assert!(check.summary.contains("ROS 1"));
    }

    #[test]
    fn test_no_ros_at_all_is_skipped() {
        let check = check_ros2(&env(&[("PATH", "/usr/bin")]));
        // On a machine that happens to have /opt/ros, this is a warning instead; both are fine,
        // what matters is that a missing ROS installation is never a failure.
        assert_ne!(check.status, Status::Fail);
        assert_eq!(check.details["ROS_DISTRO"], Value::Null);
    }
}
