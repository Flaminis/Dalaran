//! `dalaran doctor`: diagnose a Dalaran installation from the viewer binary itself.

mod endpoint;
mod environment;
mod graphics;
mod recording;
mod report;

use std::path::PathBuf;

pub use self::report::{Check, Report, Status};

// ---

/// Diagnose this Dalaran installation and print a report.
///
/// Most "Dalaran does not work" reports come down to a handful of environment problems: a GPU
/// driver that wgpu cannot use, a headless machine without a display, a stale `RERUN_*`
/// environment variable left over from a migration, a firewalled gRPC port, or a recording that
/// was truncated before it was flushed. This command checks all of that in one go, without needing
/// a working Python installation.
///
/// The exit code is non-zero only when something is actually broken. Warnings keep it at zero, so
/// this is safe to run in CI.
///
/// Examples:
///
/// * Check the installation:
///   `dalaran doctor`
///
/// * Check a recording someone sent you:
///   `dalaran doctor session.dlr`
///
/// * Machine-readable output for CI, with no network access:
///   `dalaran doctor --json --no-network`
///
/// * Check that a viewer is listening where you think it is:
///   `dalaran doctor --endpoint dalaran+http://127.0.0.1:9876/proxy`
#[derive(Debug, Clone, clap::Parser)]
pub struct DoctorCommand {
    /// Recordings to validate, e.g. `session.dlr`.
    ///
    /// Legacy Rerun `.rrd`/`.rbl` files are accepted too; they use the same framing.
    #[arg(value_name = "FILE")]
    recordings: Vec<PathBuf>,

    /// Emit a machine-readable report instead of the human-readable one.
    ///
    /// The schema is shared with the `dalaran-doctor` Python script.
    #[arg(long)]
    json: bool,

    /// Print the structured details of every check, not just its summary.
    #[arg(long, short = 'v')]
    verbose: bool,

    /// Do not touch the network. Any endpoint probe is reported as skipped.
    #[arg(long)]
    no_network: bool,

    /// A gRPC endpoint to probe, e.g. `dalaran+http://127.0.0.1:9876/proxy`.
    ///
    /// Without this, no connection is attempted at all.
    #[arg(long, value_name = "URL")]
    endpoint: Option<String>,
}

impl DoctorCommand {
    /// Runs every check and prints the report, returning the process exit code.
    pub fn run(
        &self,
        build_info: &dl_build_info::BuildInfo,
        tokio_runtime: &tokio::runtime::Handle,
    ) -> u8 {
        let report = self.diagnose(build_info, tokio_runtime);

        if self.json {
            println!("{:#}", report.to_json());
        } else {
            println!(
                "{}",
                report.to_text(report::TextOptions {
                    color: report::supports_color(),
                    verbose: self.verbose,
                })
            );
        }

        report.exit_code()
    }

    /// Runs every check, without printing anything.
    fn diagnose(
        &self,
        build_info: &dl_build_info::BuildInfo,
        tokio_runtime: &tokio::runtime::Handle,
    ) -> Report {
        let env = environment::snapshot();

        let mut checks = vec![
            check_build(build_info),
            graphics::check_graphics(tokio_runtime),
            environment::check_environment(&env),
            environment::check_display(&env),
            environment::check_ros2(&env),
        ];

        checks.extend(
            self.recordings
                .iter()
                .map(|path| recording::check_recording(path)),
        );

        checks.push(self.check_endpoint());

        Report {
            dalaran_version: build_info.version.to_string(),
            checks,
        }
    }
}

impl DoctorCommand {
    /// Probes `--endpoint`, unless there is nothing to probe or we are not allowed to.
    fn check_endpoint(&self) -> Check {
        let Some(endpoint) = &self.endpoint else {
            return Check::new(
                "endpoint",
                Status::Skip,
                "no --endpoint given, so no connection was attempted",
            );
        };

        if self.no_network {
            return Check::new(
                "endpoint",
                Status::Skip,
                "network probe skipped (--no-network)",
            )
            .with_detail("endpoint", endpoint.as_str());
        }

        endpoint::check_endpoint(endpoint)
    }
}

/// Reports what this binary actually is: version, git hash, target, and enabled features.
///
/// This is the first thing to ask for in a bug report, and the one thing a user cannot easily
/// look up themselves.
fn check_build(build_info: &dl_build_info::BuildInfo) -> Check {
    let features = build_info
        .features
        .split_whitespace()
        .map(serde_json::Value::from)
        .collect::<Vec<_>>();

    // Every "the viewer is unusably slow" report we have seen from a source checkout came down to
    // an accidental debug build, so it is worth a warning even though nothing is actually broken.
    let (status, summary) = if build_info.is_debug_build {
        (
            Status::Warn,
            format!("dalaran {} (unoptimized debug build)", build_info.version),
        )
    } else {
        (Status::Ok, format!("dalaran {}", build_info.version))
    };

    let check = Check::new("build", status, summary)
        .with_detail("version", build_info.version.to_string())
        .with_detail("crate", build_info.crate_name.as_ref())
        .with_detail("git_hash", nonempty(&build_info.git_hash))
        .with_detail("git_branch", nonempty(&build_info.git_branch))
        .with_detail("target_triple", nonempty(&build_info.target_triple))
        .with_detail("rustc_version", nonempty(&build_info.rustc_version))
        .with_detail("build_datetime", nonempty(&build_info.datetime))
        .with_detail("debug_build", build_info.is_debug_build)
        .with_detail("features", features);

    if build_info.is_debug_build {
        check.with_hint(
            "Debug builds are 10-100x slower than release ones; rebuild with `--release`.",
        )
    } else {
        check
    }
}

/// `None` for the empty strings `dl_build_info` uses to mean "unknown".
fn nonempty(value: &str) -> serde_json::Value {
    if value.is_empty() {
        serde_json::Value::Null
    } else {
        serde_json::Value::from(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn build_info(is_debug_build: bool) -> dl_build_info::BuildInfo {
        dl_build_info::BuildInfo {
            crate_name: "dalaran".into(),
            features: "run sdk".into(),
            version: dl_build_info::CrateVersion::LOCAL,
            rustc_version: "1.95.0".into(),
            llvm_version: "20.0".into(),
            git_hash: String::new().into(),
            git_branch: "main".into(),
            is_in_dalaran_workspace: true,
            target_triple: "aarch64-apple-darwin".into(),
            datetime: "2024-01-01T00:00:00Z".into(),
            is_debug_build,
        }
    }

    fn command(args: &[&str]) -> DoctorCommand {
        use clap::Parser as _;

        #[derive(Debug, clap::Parser)]
        struct Wrapper {
            #[command(subcommand)]
            command: Sub,
        }

        #[derive(Debug, clap::Subcommand)]
        enum Sub {
            Doctor(DoctorCommand),
        }

        let Sub::Doctor(command) = Wrapper::parse_from(args).command;
        command
    }

    #[test]
    fn test_parses_flags_and_files() {
        let command = command(&[
            "dalaran",
            "doctor",
            "a.dlr",
            "b.rrd",
            "--json",
            "-v",
            "--no-network",
            "--endpoint",
            "dalaran+http://127.0.0.1:9876/proxy",
        ]);
        assert_eq!(
            command.recordings,
            vec![PathBuf::from("a.dlr"), PathBuf::from("b.rrd")]
        );
        assert!(command.json);
        assert!(command.verbose);
        assert!(command.no_network);
        assert_eq!(
            command.endpoint.as_deref(),
            Some("dalaran+http://127.0.0.1:9876/proxy")
        );
    }

    #[test]
    fn test_defaults_touch_nothing() {
        let command = command(&["dalaran", "doctor"]);
        assert!(command.recordings.is_empty());
        assert!(!command.json);
        assert!(!command.verbose);
        assert!(!command.no_network);
        assert_eq!(command.endpoint, None);
    }

    #[test]
    fn test_build_check_reports_the_running_binary() {
        let check = check_build(&build_info(false));
        assert_eq!(check.status, Status::Ok);
        assert_eq!(check.details["target_triple"], "aarch64-apple-darwin");
        assert_eq!(check.details["git_hash"], serde_json::Value::Null);
        assert_eq!(check.details["features"], serde_json::json!(["run", "sdk"]));
        assert_eq!(check.details["debug_build"], false);
    }

    #[test]
    fn test_debug_builds_warn_but_still_exit_zero() {
        let check = check_build(&build_info(true));
        assert_eq!(check.status, Status::Warn);
        assert!(check.hint.is_some());
        assert_eq!(check.details["debug_build"], true);

        let report = Report {
            dalaran_version: "0.1.0".to_owned(),
            checks: vec![check],
        };
        assert_eq!(report.exit_code(), 0);
    }

    #[test]
    fn test_diagnose_produces_a_well_formed_report() {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap();

        let report = command(&["dalaran", "doctor", "--no-network"])
            .diagnose(&build_info(false), runtime.handle());

        // Every check must have a distinct name, so that `--json` consumers can index by it.
        let names = report
            .checks
            .iter()
            .map(|check| check.name)
            .collect::<std::collections::BTreeSet<_>>();
        assert_eq!(names.len(), report.checks.len(), "duplicate check names");

        assert!(names.contains("build"));
        assert!(names.contains("environment"));
        assert!(report.to_json()["checks"].is_array());
    }
}
