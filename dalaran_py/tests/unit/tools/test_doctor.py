"""Tests for `dalaran-doctor`: report schema, individual checks and exit codes."""

from __future__ import annotations

import json
import socket
from typing import TYPE_CHECKING, Any

import pytest

from ._tool_import import load_tool

if TYPE_CHECKING:
    from pathlib import Path

doctor = load_tool("doctor")


def assert_valid_check(check: dict[str, Any]) -> None:
    assert set(check) == {"name", "status", "summary", "details", "hint"}
    assert check["status"] in doctor.STATUSES
    assert isinstance(check["name"], str) and check["name"]
    assert isinstance(check["summary"], str) and check["summary"]
    assert isinstance(check["details"], dict)
    assert check["hint"] is None or isinstance(check["hint"], str)


def test_report_schema() -> None:
    report = doctor.run_checks(skip_network=True)
    assert set(report) == {"schema_version", "status", "dalaran_version", "checks"}
    assert report["schema_version"] == doctor.REPORT_SCHEMA_VERSION
    assert report["status"] in {"ok", "warn", "fail"}
    assert [check["name"] for check in report["checks"]] == [
        "python",
        "sdk",
        "viewer",
        "graphics",
        "display",
        "ros2",
        "environment",
        "endpoint",
    ]
    for check in report["checks"]:
        assert_valid_check(check)


def test_report_is_json_serializable() -> None:
    report = doctor.run_checks(skip_network=True)
    assert json.loads(json.dumps(report)) == report


def test_cli_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = doctor.main(["--json", "--no-network"])
    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == doctor.REPORT_SCHEMA_VERSION
    assert exit_code == (1 if report["status"] == "fail" else 0)


def test_cli_text_output_mentions_every_check(capsys: pytest.CaptureFixture[str]) -> None:
    doctor.main(["--no-network", "--verbose"])
    out = capsys.readouterr().out
    for name in ("python", "sdk", "viewer", "graphics", "display", "ros2", "environment", "endpoint"):
        assert name in out


def test_format_report_is_colorless_by_default() -> None:
    text = doctor.format_report(doctor.run_checks(skip_network=True))
    assert "\033[" not in text
    assert "\033[" in doctor.format_report(doctor.run_checks(skip_network=True), color=True)


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    [
        ("dalaran+http://127.0.0.1:9876/proxy", ("127.0.0.1", 9876)),
        ("dalaran://robot.local:1234", ("robot.local", 1234)),
        ("localhost:4242", ("localhost", 4242)),
        ("localhost", ("localhost", 9876)),
    ],
)
def test_split_endpoint(endpoint: str, expected: tuple[str, int]) -> None:
    assert doctor._split_endpoint(endpoint) == expected


def test_split_endpoint_rejects_garbage() -> None:
    with pytest.raises(doctor.ToolError):
        doctor._split_endpoint("dalaran://host:not-a-port")


def test_endpoint_check_detects_a_listener() -> None:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        check = doctor.check_endpoint(f"dalaran://127.0.0.1:{port}")
    assert check["status"] == "ok"
    assert check["details"]["port"] == port

    # The socket is closed again by now, so the very same address must fail.
    closed = doctor.check_endpoint(f"dalaran://127.0.0.1:{port}", timeout=0.25)
    assert closed["status"] == "warn"
    assert "error" in closed["details"]


def test_environment_check_flags_stale_rerun_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RERUN_STRICT", "1")
    check = doctor.check_environment()
    assert check["status"] == "warn"
    assert check["details"]["stale_rerun_vars"] == ["RERUN_STRICT"]


def test_environment_check_flags_unknown_and_malformed_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DALARAN_STIRCT", "1")
    assert doctor.check_environment()["details"]["unknown_vars"] == ["DALARAN_STIRCT"]

    monkeypatch.setenv("DALARAN_FLUSH_NUM_ROWS", "many")
    check = doctor.check_environment()
    assert check["status"] == "fail"
    assert check["details"]["malformed_vars"] == ["DALARAN_FLUSH_NUM_ROWS"]


def test_environment_check_accepts_known_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(doctor.KNOWN_ENV_VARS):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DALARAN_FLUSH_NUM_ROWS", "1024")
    check = doctor.check_environment()
    assert check["status"] == "ok"
    assert check["details"]["dalaran_vars"] == {"DALARAN_FLUSH_NUM_ROWS": "1024"}


def test_viewer_check_reports_incompatible_versions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_viewer = tmp_path / "dalaran"
    fake_viewer.write_text("#!/bin/sh\necho 'dalaran-cli 99.0.0'\n", encoding="utf-8")
    fake_viewer.chmod(0o755)
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: str(fake_viewer))

    check = doctor.check_viewer()
    assert check["status"] == "fail"
    assert check["details"]["compatible"] is False


def test_viewer_check_warns_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: None)
    check = doctor.check_viewer()
    assert check["status"] == "warn"
    assert check["hint"]


def test_python_and_display_checks_are_well_formed() -> None:
    for check in (doctor.check_python(), doctor.check_display(), doctor.check_graphics(), doctor.check_ros2()):
        assert_valid_check(check)
