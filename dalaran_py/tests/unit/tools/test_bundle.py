"""Tests for `dalaran-pack` / `dalaran-unpack` bundles: round-trip, verification and tamper detection."""

from __future__ import annotations

import json
import zipfile
from typing import TYPE_CHECKING

import pytest

from ._tool_import import load_tool

if TYPE_CHECKING:
    from pathlib import Path

bundle = load_tool("bundle")


def make_recording(path: Path, *, entity: str = "/world/points", timeline: str = "log_time") -> Path:
    """
    Write a minimal file with a valid Dalaran stream header.

    The payload is not a real Arrow stream, but it embeds the metadata keys the
    summarizer scans for, which is exactly the surface we want to test here.
    """
    header = b"RRF2" + bytes([0, 36, 0, 0]) + bytes([0, 0, 0, 0])
    body = b""
    for key, value in ((b"dalaran:entity_path", entity), (b"dalaran:index_name", timeline)):
        encoded = value.encode("utf-8")
        body += key + b"\x00" + len(encoded).to_bytes(4, "little") + encoded
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + body)
    return path


@pytest.fixture
def recording(tmp_path: Path) -> Path:
    return make_recording(tmp_path / "drive_01.dlr")


def test_summarize_recording(recording: Path) -> None:
    summary = bundle.summarize_recording(recording)
    assert summary["fourcc"] == "RRF2"
    assert summary["encoded_version"] == "0.36.0"
    assert summary["entity_paths"] == ["/world/points"]
    assert summary["timelines"] == ["log_time"]
    assert summary["time_ranges"] == {"log_time": None}
    assert summary["complete"] is True


def test_summarize_rejects_foreign_files(tmp_path: Path) -> None:
    bogus = tmp_path / "not_a_recording.dlr"
    bogus.write_bytes(b"PK\x03\x04 definitely not a recording")
    with pytest.raises(bundle.ToolError, match="not a Dalaran recording"):
        bundle.summarize_recording(bogus)


def test_round_trip(tmp_path: Path, recording: Path) -> None:
    blueprint = tmp_path / "overview.dbl"
    blueprint.write_bytes(b"blueprint bytes")
    calibration = tmp_path / "calibration.yaml"
    calibration.write_text("camera:\n  fx: 600.0\n", encoding="utf-8")

    out = tmp_path / "session.dlrpack"
    manifest = bundle.create_bundle(
        out,
        [recording],
        blueprints=[blueprint],
        attachments=[calibration],
        description="a short drive",
        tags=["lidar", "outdoor", "lidar"],
    )

    assert out.is_file()
    assert manifest["kind"] == "dalaran.bundle"
    assert manifest["schema_version"] == bundle.SCHEMA_VERSION
    assert manifest["tags"] == ["lidar", "outdoor"]
    assert [entry["path"] for entry in manifest["files"]] == [
        "recordings/drive_01.dlr",
        "blueprints/overview.dbl",
        "attachments/calibration.yaml",
    ]
    assert manifest["files"][0]["recording"]["entity_paths"] == ["/world/points"]

    assert bundle.verify_bundle(out) == []

    dest = tmp_path / "unpacked"
    written = bundle.extract_bundle(out, dest)
    assert (dest / "recordings" / "drive_01.dlr").read_bytes() == recording.read_bytes()
    assert (dest / "attachments" / "calibration.yaml").read_text(encoding="utf-8").startswith("camera:")
    assert set(written) == {path.resolve() for path in dest.rglob("*") if path.is_file()}


def test_inspect_matches_created_manifest(tmp_path: Path, recording: Path) -> None:
    out = tmp_path / "session.dlrpack"
    created = bundle.create_bundle(out, [recording])
    assert bundle.inspect_bundle(out) == created


def test_duplicate_names_are_disambiguated(tmp_path: Path) -> None:
    first = make_recording(tmp_path / "a" / "drive.dlr")
    second = make_recording(tmp_path / "b" / "drive.dlr", entity="/world/other")
    out = tmp_path / "session.dlrpack"
    manifest = bundle.create_bundle(out, [first, second])
    assert [entry["path"] for entry in manifest["files"]] == [
        "recordings/drive.dlr",
        "recordings/drive_1.dlr",
    ]
    assert bundle.verify_bundle(out) == []


def test_requires_a_recording(tmp_path: Path) -> None:
    with pytest.raises(bundle.ToolError, match="at least one"):
        bundle.create_bundle(tmp_path / "empty.dlrpack", [])


def test_refuses_to_overwrite(tmp_path: Path, recording: Path) -> None:
    out = tmp_path / "session.dlrpack"
    bundle.create_bundle(out, [recording])
    with pytest.raises(bundle.ToolError, match="already exists"):
        bundle.create_bundle(out, [recording])
    bundle.create_bundle(out, [recording], overwrite=True)


def _rewrite_member(path: Path, member: str, data: bytes) -> None:
    with zipfile.ZipFile(path, "r") as source:
        contents = {name: source.read(name) for name in source.namelist()}
    contents[member] = data
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as sink:
        for name, blob in contents.items():
            sink.writestr(name, blob)


def test_tampered_payload_is_detected(tmp_path: Path, recording: Path) -> None:
    out = tmp_path / "session.dlrpack"
    bundle.create_bundle(out, [recording])
    original = recording.read_bytes()
    _rewrite_member(out, "recordings/drive_01.dlr", original + b"evil")

    problems = bundle.verify_bundle(out)
    assert any("checksum mismatch" in problem for problem in problems)
    assert any("size mismatch" in problem for problem in problems)

    with pytest.raises(bundle.ToolError, match="failed verification"):
        bundle.extract_bundle(out, tmp_path / "dest")

    # ... but the user can still force it out if they know what they are doing.
    bundle.extract_bundle(out, tmp_path / "dest", verify=False)


def test_missing_and_extra_members_are_detected(tmp_path: Path, recording: Path) -> None:
    out = tmp_path / "session.dlrpack"
    manifest = bundle.create_bundle(out, [recording])

    with zipfile.ZipFile(out, "r") as source:
        contents = {name: source.read(name) for name in source.namelist()}
    del contents["recordings/drive_01.dlr"]
    contents["recordings/smuggled.dlr"] = b"RRF2"
    with zipfile.ZipFile(out, "w") as sink:
        for name, blob in contents.items():
            sink.writestr(name, blob)

    problems = bundle.verify_bundle(out)
    assert any("missing from the archive" in problem for problem in problems)
    assert any("missing from the manifest" in problem for problem in problems)
    assert manifest["files"][0]["path"] == "recordings/drive_01.dlr"


def test_rejects_non_bundles(tmp_path: Path, recording: Path) -> None:
    with pytest.raises(bundle.ToolError, match="no such file"):
        bundle.inspect_bundle(tmp_path / "nope.dlrpack")

    with pytest.raises(bundle.ToolError, match="not a zip archive"):
        bundle.inspect_bundle(recording)

    plain_zip = tmp_path / "plain.dlrpack"
    with zipfile.ZipFile(plain_zip, "w") as archive:
        archive.writestr("hello.txt", "hi")
    with pytest.raises(bundle.ToolError, match=r"manifest\.json is missing"):
        bundle.inspect_bundle(plain_zip)


def test_rejects_future_schema_versions(tmp_path: Path, recording: Path) -> None:
    out = tmp_path / "session.dlrpack"
    manifest = bundle.create_bundle(out, [recording])
    manifest["schema_version"] = bundle.SCHEMA_VERSION + 1
    _rewrite_member(out, bundle.MANIFEST_NAME, json.dumps(manifest).encode("utf-8"))
    with pytest.raises(bundle.ToolError, match="newer than this tool supports"):
        bundle.inspect_bundle(out)


def test_refuses_path_traversal(tmp_path: Path, recording: Path) -> None:
    out = tmp_path / "session.dlrpack"
    manifest = bundle.create_bundle(out, [recording])
    manifest["files"][0]["path"] = "../escaped.dlr"
    _rewrite_member(out, bundle.MANIFEST_NAME, json.dumps(manifest).encode("utf-8"))
    with pytest.raises(bundle.ToolError):
        bundle.extract_bundle(out, tmp_path / "dest", verify=False)


def test_cli_pack_inspect_verify_and_unpack(
    tmp_path: Path, recording: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "session.dlrpack"
    assert bundle.main_pack([str(out), str(recording), "--tag", "lidar", "--json"]) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["tags"] == ["lidar"]

    assert bundle.main_unpack([str(out), "--inspect"]) == 0
    assert "Dalaran bundle" in capsys.readouterr().out

    assert bundle.main_unpack([str(out), "--verify"]) == 0
    assert "ok" in capsys.readouterr().out

    dest = tmp_path / "dest"
    assert bundle.main_unpack([str(out), "-d", str(dest)]) == 0
    capsys.readouterr()
    assert (dest / "recordings" / "drive_01.dlr").is_file()

    # A second extraction must not silently clobber files.
    assert bundle.main_unpack([str(out), "-d", str(dest)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert bundle.main_unpack([str(out), "-d", str(dest), "--force"]) == 0


def test_cli_verify_reports_failure(tmp_path: Path, recording: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "session.dlrpack"
    bundle.create_bundle(out, [recording])
    _rewrite_member(out, "recordings/drive_01.dlr", b"RRF2 tampered")
    assert bundle.main_unpack([str(out), "--verify"]) == 1
    assert "FAILED" in capsys.readouterr().err
