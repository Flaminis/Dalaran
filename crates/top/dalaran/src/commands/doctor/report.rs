//! The report produced by `dalaran doctor`, and how it is rendered.
//!
//! The JSON schema here is deliberately identical to the one emitted by the Python
//! `dalaran.tools.doctor` module: same `schema_version`, same top-level keys, and the same
//! per-check shape (`name`, `status`, `summary`, `details`, `hint`). A tool that consumes one
//! must be able to consume the other without special-casing, so please bump
//! [`REPORT_SCHEMA_VERSION`] on both sides at once if the shape ever has to change.

use std::io::IsTerminal as _;

use serde_json::{Map, Value, json};

/// Version of the `--json` report schema.
///
/// Kept in sync with `dalaran.tools.doctor.REPORT_SCHEMA_VERSION`.
pub const REPORT_SCHEMA_VERSION: u32 = 1;

/// The outcome of a single check, in increasing order of severity (`Skip` aside).
///
/// The derived ordering is what decides the overall status of a [`Report`], so the declaration
/// order matters: it mirrors `dalaran.tools.doctor._SEVERITY`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Status {
    /// The check does not apply here, e.g. a network probe under `--no-network`.
    Skip,

    /// Everything is as it should be.
    Ok,

    /// Suspicious, but not broken. Never affects the exit code.
    Warn,

    /// Actually broken. Makes `dalaran doctor` exit non-zero.
    Fail,
}

impl Status {
    /// The value used in the `--json` output.
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Skip => "skip",
            Self::Ok => "ok",
            Self::Warn => "warn",
            Self::Fail => "fail",
        }
    }

    /// The fixed-width label used in the human-readable output.
    fn label(self) -> &'static str {
        match self {
            Self::Skip => "skip",
            Self::Ok => "ok  ",
            Self::Warn => "warn",
            Self::Fail => "FAIL",
        }
    }

    /// The ANSI style the label is printed in, when colors are enabled.
    fn style(self) -> Style {
        match self {
            Self::Skip => Style::Dim,
            Self::Ok => Style::Green,
            Self::Warn => Style::Yellow,
            Self::Fail => Style::Red,
        }
    }
}

/// The handful of ANSI styles we use, mirroring `dalaran.tools._common._ANSI`.
#[derive(Clone, Copy, Debug)]
enum Style {
    Bold,
    Dim,
    Red,
    Green,
    Yellow,
}

impl Style {
    fn code(self) -> &'static str {
        match self {
            Self::Bold => "\x1b[1m",
            Self::Dim => "\x1b[2m",
            Self::Red => "\x1b[31m",
            Self::Green => "\x1b[32m",
            Self::Yellow => "\x1b[33m",
        }
    }
}

/// Wraps `text` in an ANSI style, or returns it unchanged when `enabled` is false.
fn colorize(text: &str, style: Style, enabled: bool) -> String {
    if enabled {
        format!("{}{text}\x1b[0m", style.code())
    } else {
        text.to_owned()
    }
}

/// Whether ANSI escape codes should be written to stdout.
///
/// Honors the `NO_COLOR` and `FORCE_COLOR` conventions before falling back to a TTY check, exactly
/// like `dalaran.tools._common.supports_color` does, so that piping into a file or a CI log gives
/// readable output.
pub fn supports_color() -> bool {
    if std::env::var_os("NO_COLOR").is_some_and(|value| !value.is_empty()) {
        return false;
    }
    if std::env::var_os("FORCE_COLOR").is_some_and(|value| !value.is_empty()) {
        return true;
    }
    std::io::stdout().is_terminal()
}

/// The result of one diagnostic.
#[derive(Clone, Debug)]
pub struct Check {
    /// Stable machine-readable identifier, e.g. `graphics`.
    pub name: &'static str,

    /// How bad it is.
    pub status: Status,

    /// One line, suitable for a terminal.
    pub summary: String,

    /// Structured extras, shown by `--verbose` and always present in `--json`.
    pub details: Map<String, Value>,

    /// What the user should do about it. Only shown for `warn`/`fail`.
    pub hint: Option<String>,
}

impl Check {
    /// Starts a new check; add details and a hint with the builder methods.
    pub fn new(name: &'static str, status: Status, summary: impl Into<String>) -> Self {
        Self {
            name,
            status,
            summary: summary.into(),
            details: Map::new(),
            hint: None,
        }
    }

    /// Attaches one structured detail. Later writes to the same key win.
    #[must_use]
    pub fn with_detail(mut self, key: &str, value: impl Into<Value>) -> Self {
        self.details.insert(key.to_owned(), value.into());
        self
    }

    /// Overrides the status and summary, keeping the details gathered so far.
    ///
    /// Checks generally collect all their evidence first and only then decide what it means, so
    /// this lets them build the details once instead of once per outcome.
    #[must_use]
    pub fn with_status(mut self, status: Status, summary: impl Into<String>) -> Self {
        self.status = status;
        self.summary = summary.into();
        self
    }

    /// Attaches the actionable advice shown under a `warn` or `fail` line.
    #[must_use]
    pub fn with_hint(mut self, hint: impl Into<String>) -> Self {
        self.hint = Some(hint.into());
        self
    }

    fn to_json(&self) -> Value {
        json!({
            "name": self.name,
            "status": self.status.as_str(),
            "summary": self.summary,
            "details": Value::Object(self.details.clone()),
            "hint": self.hint,
        })
    }
}

/// Everything `dalaran doctor` found out, ready to be printed or serialized.
#[derive(Clone, Debug)]
pub struct Report {
    /// Version of the `dalaran` build that produced this report.
    pub dalaran_version: String,

    /// One entry per diagnostic, in the order they were run.
    pub checks: Vec<Check>,
}

impl Report {
    /// The worst status of any check.
    ///
    /// A report that is nothing but skips is reported as `ok`: skipping a network probe is not a
    /// diagnosis.
    pub fn status(&self) -> Status {
        let worst = self
            .checks
            .iter()
            .map(|check| check.status)
            .max()
            .unwrap_or(Status::Ok);
        if worst == Status::Skip {
            Status::Ok
        } else {
            worst
        }
    }

    /// The process exit code: non-zero only if something is actually broken.
    ///
    /// Warnings deliberately keep this at zero so that `dalaran doctor` can be dropped into a CI
    /// pipeline without turning every headless machine into a red build.
    pub fn exit_code(&self) -> u8 {
        u8::from(self.status() == Status::Fail)
    }

    /// The machine-readable report; see [`REPORT_SCHEMA_VERSION`].
    pub fn to_json(&self) -> Value {
        json!({
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": self.status().as_str(),
            "dalaran_version": self.dalaran_version,
            "checks": self.checks.iter().map(Check::to_json).collect::<Vec<_>>(),
        })
    }

    /// The human-readable report.
    pub fn to_text(&self, color: bool, verbose: bool) -> String {
        let mut lines = vec![
            colorize(
                &format!("dalaran doctor  (dalaran {})", self.dalaran_version),
                Style::Bold,
                color,
            ),
            String::new(),
        ];

        for check in &self.checks {
            let label = colorize(check.status.label(), check.status.style(), color);
            lines.push(format!(
                "[{label}] {name:<12} {summary}",
                name = check.name,
                summary = check.summary,
            ));

            if let Some(hint) = &check.hint
                && matches!(check.status, Status::Warn | Status::Fail)
            {
                lines.push(format!(
                    "       {}",
                    colorize(&format!("hint: {hint}"), Style::Dim, color)
                ));
            }

            if verbose {
                for (key, value) in &check.details {
                    lines.push(format!("       {key}: {}", render_detail(value)));
                }
            }
        }

        let failures = self
            .checks
            .iter()
            .filter(|check| check.status == Status::Fail)
            .map(|check| check.name)
            .collect::<Vec<_>>();

        lines.push(String::new());
        if failures.is_empty() {
            lines.push(colorize("no failures", Style::Green, color));
        } else {
            lines.push(colorize(
                &format!(
                    "{} check(s) failed: {}",
                    failures.len(),
                    failures.join(", ")
                ),
                Style::Red,
                color,
            ));
        }

        lines.join("\n")
    }
}

/// Renders a detail value for the human-readable `--verbose` output.
///
/// Strings are printed bare, because quoting every path and version string makes the output much
/// harder to skim. Everything else falls back to its JSON spelling.
fn render_detail(value: &Value) -> String {
    match value {
        Value::String(text) => text.clone(),
        Value::Null => "none".to_owned(),
        other => other.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn check(name: &'static str, status: Status) -> Check {
        Check::new(name, status, format!("{name} is {}", status.as_str()))
    }

    #[test]
    fn test_worst_status_wins() {
        let report = Report {
            dalaran_version: "0.1.0".to_owned(),
            checks: vec![
                check("a", Status::Ok),
                check("b", Status::Warn),
                check("c", Status::Ok),
            ],
        };
        assert_eq!(report.status(), Status::Warn);

        let report = Report {
            checks: vec![check("a", Status::Fail), check("b", Status::Warn)],
            ..report
        };
        assert_eq!(report.status(), Status::Fail);
    }

    #[test]
    fn test_only_failures_are_non_zero() {
        for (status, expected) in [
            (Status::Skip, 0),
            (Status::Ok, 0),
            (Status::Warn, 0),
            (Status::Fail, 1),
        ] {
            let report = Report {
                dalaran_version: "0.1.0".to_owned(),
                checks: vec![check("a", status)],
            };
            assert_eq!(report.exit_code(), expected, "{status:?}");
        }
    }

    #[test]
    fn test_a_report_of_only_skips_is_ok() {
        let report = Report {
            dalaran_version: "0.1.0".to_owned(),
            checks: vec![check("a", Status::Skip)],
        };
        assert_eq!(report.status(), Status::Ok);
        assert_eq!(report.exit_code(), 0);
    }

    #[test]
    fn test_json_schema_shape_is_stable() {
        let report = Report {
            dalaran_version: "0.1.0".to_owned(),
            checks: vec![
                check("a", Status::Ok).with_detail("count", 3),
                check("b", Status::Warn).with_hint("do the thing"),
            ],
        };

        let json = report.to_json();
        assert_eq!(json["schema_version"], json!(REPORT_SCHEMA_VERSION));
        assert_eq!(json["status"], json!("warn"));
        assert_eq!(json["dalaran_version"], json!("0.1.0"));

        let checks = json["checks"].as_array().unwrap();
        assert_eq!(checks.len(), 2);
        for check in checks {
            let object = check.as_object().unwrap();
            let mut keys = object.keys().cloned().collect::<Vec<_>>();
            keys.sort();
            assert_eq!(keys, ["details", "hint", "name", "status", "summary"]);
            assert!(object["details"].is_object());
        }

        assert_eq!(checks[0]["details"]["count"], json!(3));
        assert_eq!(checks[0]["hint"], Value::Null);
        assert_eq!(checks[1]["hint"], json!("do the thing"));
    }

    #[test]
    fn test_text_output_has_a_status_column_and_no_escapes_without_color() {
        let report = Report {
            dalaran_version: "0.1.0".to_owned(),
            checks: vec![
                check("good", Status::Ok).with_detail("where", "here"),
                check("bad", Status::Fail).with_hint("fix it"),
            ],
        };

        let text = report.to_text(false, true);
        assert!(!text.contains('\x1b'), "colors leaked: {text}");
        assert!(text.contains("[ok  ] good"), "{text}");
        assert!(text.contains("[FAIL] bad"), "{text}");
        assert!(text.contains("hint: fix it"), "{text}");
        assert!(text.contains("where: here"), "{text}");
        assert!(text.contains("1 check(s) failed: bad"), "{text}");

        // Hints only show up for warnings and failures.
        let quiet = Report {
            dalaran_version: "0.1.0".to_owned(),
            checks: vec![check("good", Status::Ok).with_hint("ignored")],
        }
        .to_text(false, false);
        assert!(!quiet.contains("ignored"), "{quiet}");
        assert!(quiet.contains("no failures"), "{quiet}");

        assert!(report.to_text(true, false).contains('\x1b'));
    }
}
