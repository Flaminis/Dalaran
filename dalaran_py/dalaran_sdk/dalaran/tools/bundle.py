"""
Portable `.dlrpack` dataset bundles.

A bundle is a plain zip archive that carries a set of Dalaran recordings
together with everything needed to replay them somewhere else: optional
blueprints, arbitrary attachments (calibration files, notes, ...) and a
`manifest.json` describing the contents, including a SHA-256 for every file.

This is the format robotics teams use to hand a reproducible recording to a
colleague, attach it to a bug report, or archive it next to a dataset. Because
it is "just a zip", it can be opened with any tool; because it has a manifest
with checksums, `dalaran-unpack --verify` can prove that it arrived intact.

Layout
------
```text
my_session.dlrpack
+-- manifest.json
+-- recordings/drive_01.dlr
+-- blueprints/overview.dbl
+-- attachments/calibration.yaml
```

Example
-------
```python
from dalaran.tools.bundle import create_bundle, extract_bundle, inspect_bundle

create_bundle("session.dlrpack", ["drive_01.dlr"], tags=["lidar"])
print(inspect_bundle("session.dlrpack")["files"])
extract_bundle("session.dlrpack", "./unpacked")
```

"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._common import (
    BLUEPRINT_SUFFIX,
    BUNDLE_SUFFIX,
    RECORDING_SUFFIX,
    ToolError,
    colorize,
    human_bytes,
    sdk_version,
    sha256_file,
    supports_color,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

__all__ = [
    "MANIFEST_NAME",
    "SCHEMA_VERSION",
    "create_bundle",
    "extract_bundle",
    "inspect_bundle",
    "main_pack",
    "main_unpack",
    "summarize_recording",
    "verify_bundle",
]

MANIFEST_NAME = "manifest.json"
"""Name of the manifest member inside a `.dlrpack`."""

SCHEMA_VERSION = 1
"""Version of the manifest schema written by this module."""

BUNDLE_KIND = "dalaran.bundle"
"""Discriminator stored in the manifest so unrelated zips are rejected early."""

_DLR_FOURCC = b"RRF2"
_ENTITY_PATH_KEY = b"dalaran:entity_path"
_INDEX_NAME_KEY = b"dalaran:index_name"

_ROLE_DIRS = {
    "recording": "recordings",
    "blueprint": "blueprints",
    "attachment": "attachments",
}


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_flatbuffer_string(data: bytes, offset: int) -> str | None:
    """Read a 4-byte little-endian length-prefixed UTF-8 string at `offset`, if it looks sane."""
    if offset + 4 > len(data):
        return None
    length = int.from_bytes(data[offset : offset + 4], "little")
    if length == 0 or length > 4096 or offset + 4 + length > len(data):
        return None
    try:
        text = data[offset + 4 : offset + 4 + length].decode("utf-8")
    except UnicodeDecodeError:
        return None
    if any(char < " " for char in text):
        return None
    return text


def _scan_metadata_values(data: bytes, key: bytes) -> list[str]:
    """
    Collect the values stored right after every occurrence of an Arrow metadata `key`.

    Arrow schemas serialize metadata as a flatbuffer vector of `KeyValue` tables,
    and both the key and the value are length-prefixed strings laid out next to
    each other. Reading them this way lets us summarize a recording without
    pulling in `pyarrow` or the compiled Dalaran bindings. It is best-effort by
    construction: anything that does not decode cleanly is simply skipped.
    """
    values: list[str] = []
    start = 0
    while True:
        found = data.find(key, start)
        if found < 0:
            return values
        start = found + len(key)
        # Strings are 4-byte aligned and NUL-padded up to the next boundary.
        cursor = start
        while cursor < len(data) and data[cursor] == 0:
            cursor += 1
        value = _read_flatbuffer_string(data, cursor)
        if value is not None:
            values.append(value)


def summarize_recording(path: str | Path) -> dict[str, Any]:
    """
    Describe a `.dlr` recording without decoding it fully.

    The stream header is parsed authoritatively (magic bytes and the encoding
    version), while entity paths and timeline names are recovered with a
    best-effort scan of the uncompressed Arrow schema metadata. When the scan
    cannot see anything, `complete` is `False` and the lists are empty, but the
    header fields are still trustworthy.

    Parameters
    ----------
    path:
        Path to a `.dlr` recording.

    Returns
    -------
    dict
        Keys: `fourcc`, `encoded_version`, `entity_paths`, `timelines`,
        `time_ranges` and `complete`.

    Raises
    ------
    ToolError
        If the file is too short or does not start with the Dalaran magic bytes.

    Example
    -------
    ```python
    from dalaran.tools.bundle import summarize_recording

    summary = summarize_recording("drive_01.dlr")
    print(summary["encoded_version"], summary["entity_paths"])
    ```

    """
    path = Path(path)
    data = path.read_bytes()
    if len(data) < 12:
        raise ToolError(f"{path}: too short to be a Dalaran recording ({len(data)} bytes)")
    fourcc = data[:4]
    if fourcc != _DLR_FOURCC:
        raise ToolError(
            f"{path}: not a Dalaran recording (expected magic {_DLR_FOURCC.decode()!r}, got {fourcc!r})",
        )
    major, minor, patch = data[4], data[5], data[6]

    entity_paths = sorted(set(_scan_metadata_values(data, _ENTITY_PATH_KEY)))
    timelines = sorted(set(_scan_metadata_values(data, _INDEX_NAME_KEY)))

    return {
        "fourcc": fourcc.decode("ascii"),
        "encoded_version": f"{major}.{minor}.{patch}",
        "entity_paths": entity_paths,
        "timelines": timelines,
        # Reading actual index values requires decoding the Arrow payloads, which
        # this stdlib-only tool deliberately does not do. The key is kept so the
        # schema is stable once a richer summarizer lands.
        "time_ranges": dict.fromkeys(timelines),
        "complete": bool(entity_paths or timelines),
    }


def _classify(path: Path, explicit_role: str | None = None) -> str:
    if explicit_role is not None:
        return explicit_role
    suffix = path.suffix.lower()
    if suffix == RECORDING_SUFFIX:
        return "recording"
    if suffix == BLUEPRINT_SUFFIX:
        return "blueprint"
    return "attachment"


def _unique_member(existing: set[str], role: str, name: str) -> str:
    directory = _ROLE_DIRS[role]
    stem, dot, suffix = name.partition(".")
    candidate = f"{directory}/{name}"
    counter = 1
    while candidate in existing:
        candidate = f"{directory}/{stem}_{counter}{dot}{suffix}"
        counter += 1
    existing.add(candidate)
    return candidate


def _entry_for(source: Path, member: str, role: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": member,
        "role": role,
        "source_name": source.name,
        "size_bytes": source.stat().st_size,
        "sha256": sha256_file(source),
    }
    if role == "recording":
        entry["recording"] = summarize_recording(source)
    return entry


def create_bundle(
    output: str | Path,
    recordings: Iterable[str | Path],
    *,
    blueprints: Iterable[str | Path] = (),
    attachments: Iterable[str | Path] = (),
    description: str | None = None,
    tags: Iterable[str] = (),
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Write a `.dlrpack` bundle and return the manifest that was stored in it.

    Parameters
    ----------
    output:
        Destination path. A `.dlrpack` suffix is appended when missing.
    recordings:
        One or more `.dlr` recordings. At least one is required.
    blueprints:
        Optional `.dbl` blueprint files.
    attachments:
        Arbitrary extra files (calibration, notes, ...) to carry along.
    description:
        Free-form description stored in the manifest.
    tags:
        Short labels used for searching and grouping bundles.
    overwrite:
        Allow replacing an existing file at `output`.

    Returns
    -------
    dict
        The manifest, exactly as serialized into the archive.

    Raises
    ------
    ToolError
        If no recording is given, an input is missing, or the output exists and
        `overwrite` is false.

    Example
    -------
    ```python
    from dalaran.tools.bundle import create_bundle

    manifest = create_bundle("session.dlrpack", ["drive_01.dlr"], tags=["lidar"])
    print(manifest["files"][0]["sha256"])
    ```

    """
    output = Path(output)
    if output.suffix != BUNDLE_SUFFIX:
        output = output.with_name(output.name + BUNDLE_SUFFIX)
    if output.exists() and not overwrite:
        raise ToolError(f"{output} already exists (pass overwrite=True / --force to replace it)")

    inputs: list[tuple[Path, str]] = []
    for group, role in ((recordings, "recording"), (blueprints, "blueprint"), (attachments, "attachment")):
        for item in group:
            item_path = Path(item)
            if not item_path.is_file():
                raise ToolError(f"{item_path}: no such file")
            inputs.append((item_path, _classify(item_path, role)))

    if not any(role == "recording" for _, role in inputs):
        raise ToolError("a bundle needs at least one .dlr recording")

    used: set[str] = set()
    entries = [_entry_for(source, _unique_member(used, role, source.name), role) for source, role in inputs]

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": BUNDLE_KIND,
        "created_at": _utc_now_iso(),
        "dalaran_version": sdk_version(),
        "description": description,
        "tags": sorted({str(tag) for tag in tags}),
        "files": entries,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        for (source, _role), entry in zip(inputs, entries, strict=False):
            archive.write(source, entry["path"])
    return manifest


def _load_manifest(archive: zipfile.ZipFile, bundle: Path) -> dict[str, Any]:
    try:
        raw = archive.read(MANIFEST_NAME)
    except KeyError:
        raise ToolError(f"{bundle}: not a Dalaran bundle ({MANIFEST_NAME} is missing)") from None
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ToolError(f"{bundle}: {MANIFEST_NAME} is not valid JSON: {err}") from err
    if not isinstance(manifest, dict) or manifest.get("kind") != BUNDLE_KIND:
        raise ToolError(f"{bundle}: {MANIFEST_NAME} is not a Dalaran bundle manifest")
    schema_version = manifest.get("schema_version")
    if not isinstance(schema_version, int) or schema_version > SCHEMA_VERSION:
        raise ToolError(
            f"{bundle}: manifest schema version {schema_version!r} is newer than this tool supports "
            f"(max {SCHEMA_VERSION}); please upgrade dalaran-sdk",
        )
    return manifest


def _open_bundle(path: str | Path) -> tuple[Path, zipfile.ZipFile]:
    bundle = Path(path)
    if not bundle.is_file():
        raise ToolError(f"{bundle}: no such file")
    if not zipfile.is_zipfile(bundle):
        raise ToolError(f"{bundle}: not a zip archive, so not a Dalaran bundle")
    return bundle, zipfile.ZipFile(bundle, "r")


def inspect_bundle(path: str | Path) -> dict[str, Any]:
    """
    Read the manifest of a bundle without extracting anything.

    Parameters
    ----------
    path:
        Path to a `.dlrpack` file.

    Returns
    -------
    dict
        The manifest stored in the bundle.

    Raises
    ------
    ToolError
        If the file is not a readable Dalaran bundle.

    Example
    -------
    ```python
    from dalaran.tools.bundle import inspect_bundle

    manifest = inspect_bundle("session.dlrpack")
    print(manifest["tags"])
    ```

    """
    bundle, archive = _open_bundle(path)
    with archive:
        return _load_manifest(archive, bundle)


def verify_bundle(path: str | Path) -> list[str]:
    """
    Check a bundle against its manifest and return a list of problems.

    Every declared member must be present, have the recorded size, and hash to
    the recorded SHA-256. Members present in the archive but absent from the
    manifest are reported too, since they were not signed off by the producer.

    Parameters
    ----------
    path:
        Path to a `.dlrpack` file.

    Returns
    -------
    list of str
        Human-readable problem descriptions; empty when the bundle is intact.

    Example
    -------
    ```python
    from dalaran.tools.bundle import verify_bundle

    assert verify_bundle("session.dlrpack") == []
    ```

    """
    bundle, archive = _open_bundle(path)
    problems: list[str] = []
    with archive:
        manifest = _load_manifest(archive, bundle)
        declared = {str(entry["path"]) for entry in manifest.get("files", [])}
        present = {name for name in archive.namelist() if not name.endswith("/")}

        for name in sorted(present - declared - {MANIFEST_NAME}):
            problems.append(f"{name}: present in the archive but missing from the manifest")

        for entry in manifest.get("files", []):
            member = str(entry["path"])
            if member not in present:
                problems.append(f"{member}: declared in the manifest but missing from the archive")
                continue
            digest = hashlib.sha256()
            size = 0
            with archive.open(member) as handle:
                while True:
                    block = handle.read(1 << 20)
                    if not block:
                        break
                    size += len(block)
                    digest.update(block)
            if size != entry.get("size_bytes"):
                problems.append(f"{member}: size mismatch (manifest {entry.get('size_bytes')}, archive {size})")
            if digest.hexdigest() != entry.get("sha256"):
                problems.append(f"{member}: checksum mismatch (the file was modified or is corrupt)")
    return problems


def extract_bundle(
    path: str | Path,
    dest: str | Path = ".",
    *,
    verify: bool = True,
    overwrite: bool = False,
) -> list[Path]:
    """
    Extract a bundle into `dest` and return the paths that were written.

    Parameters
    ----------
    path:
        Path to a `.dlrpack` file.
    dest:
        Destination directory; it is created if needed.
    verify:
        Validate checksums before writing anything. Recommended, and cheap.
    overwrite:
        Allow overwriting files that already exist in `dest`.

    Returns
    -------
    list of pathlib.Path
        The extracted files, including the manifest.

    Raises
    ------
    ToolError
        If verification fails, a member escapes `dest`, or a file exists and
        `overwrite` is false.

    Example
    -------
    ```python
    from dalaran.tools.bundle import extract_bundle

    for extracted in extract_bundle("session.dlrpack", "./unpacked"):
        print(extracted)
    ```

    """
    bundle, archive = _open_bundle(path)
    if verify:
        problems = verify_bundle(bundle)
        if problems:
            raise ToolError(f"{bundle} failed verification:\n  " + "\n  ".join(problems))

    dest_dir = Path(dest).resolve()
    written: list[Path] = []
    with archive:
        manifest = _load_manifest(archive, bundle)
        members = [MANIFEST_NAME] + [str(entry["path"]) for entry in manifest.get("files", [])]
        targets: list[tuple[str, Path]] = []
        for member in members:
            target = (dest_dir / member).resolve()
            if not str(target).startswith(str(dest_dir) + os.sep) and target != dest_dir:
                raise ToolError(f"{bundle}: refusing to extract {member!r} outside of {dest_dir}")
            if target.exists() and not overwrite:
                raise ToolError(f"{target} already exists (pass overwrite=True / --force to replace it)")
            targets.append((member, target))

        for member, target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, open(target, "wb") as sink:
                while True:
                    block = source.read(1 << 20)
                    if not block:
                        break
                    sink.write(block)
            written.append(target)
    return written


def format_manifest(manifest: dict[str, Any], *, color: bool = False) -> str:
    """
    Render a manifest as a compact human-readable report.

    Example
    -------
    ```python
    from dalaran.tools.bundle import format_manifest, inspect_bundle

    print(format_manifest(inspect_bundle("session.dlrpack")))
    ```

    """
    lines = [
        colorize("Dalaran bundle", "bold", enabled=color),
        f"  created at      {manifest.get('created_at')}",
        f"  dalaran version {manifest.get('dalaran_version')}",
        f"  schema version  {manifest.get('schema_version')}",
    ]
    if manifest.get("description"):
        lines.append(f"  description     {manifest['description']}")
    if manifest.get("tags"):
        lines.append(f"  tags            {', '.join(manifest['tags'])}")

    files = manifest.get("files", [])
    lines.append(colorize(f"  {len(files)} file(s)", "bold", enabled=color))
    for entry in files:
        lines.append(f"    {entry['path']}  ({entry['role']}, {human_bytes(int(entry['size_bytes']))})")
        lines.append(f"      sha256 {entry['sha256']}")
        recording = entry.get("recording")
        if recording:
            paths = recording.get("entity_paths") or []
            timelines = recording.get("timelines") or []
            lines.append(f"      encoded with dalaran {recording.get('encoded_version')}")
            if paths:
                shown = ", ".join(paths[:8]) + (" ..." if len(paths) > 8 else "")
                lines.append(f"      entities  {shown}")
            if timelines:
                lines.append(f"      timelines {', '.join(timelines)}")
    return "\n".join(lines)


def _pack_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dalaran-pack",
        description="Bundle Dalaran recordings, blueprints and attachments into a portable .dlrpack archive.",
    )
    parser.add_argument("output", help="path of the .dlrpack to write")
    parser.add_argument("recordings", nargs="+", help="one or more .dlr recordings")
    parser.add_argument("--blueprint", action="append", default=[], metavar="FILE", help="a .dbl blueprint to include")
    parser.add_argument("--attach", action="append", default=[], metavar="FILE", help="an extra file to include")
    parser.add_argument("--tag", action="append", default=[], metavar="TAG", help="a label stored in the manifest")
    parser.add_argument("--description", default=None, help="free-form description stored in the manifest")
    parser.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    parser.add_argument("--json", action="store_true", help="print the manifest as JSON instead of a report")
    return parser


def main_pack(argv: Sequence[str] | None = None) -> int:
    """
    Entry point of the `dalaran-pack` console script.

    Example
    -------
    ```python
    from dalaran.tools.bundle import main_pack

    raise SystemExit(main_pack(["session.dlrpack", "drive_01.dlr", "--tag", "lidar"]))
    ```

    """
    args = _pack_parser().parse_args(argv)
    try:
        manifest = create_bundle(
            args.output,
            args.recordings,
            blueprints=args.blueprint,
            attachments=args.attach,
            description=args.description,
            tags=args.tag,
            overwrite=args.force,
        )
    except ToolError as err:
        print(f"dalaran-pack: {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(format_manifest(manifest, color=supports_color()))
    return 0


def _unpack_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dalaran-unpack",
        description="Inspect, verify and extract portable .dlrpack bundles.",
    )
    parser.add_argument("bundle", help="path of the .dlrpack to read")
    parser.add_argument("-d", "--directory", default=".", help="directory to extract into (default: current directory)")
    parser.add_argument("--inspect", action="store_true", help="print the manifest without extracting anything")
    parser.add_argument("--verify", action="store_true", help="only validate checksums, do not extract")
    parser.add_argument("--no-verify", action="store_true", help="skip checksum validation while extracting")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    return parser


def main_unpack(argv: Sequence[str] | None = None) -> int:
    """
    Entry point of the `dalaran-unpack` console script.

    Example
    -------
    ```python
    from dalaran.tools.bundle import main_unpack

    raise SystemExit(main_unpack(["session.dlrpack", "--inspect"]))
    ```

    """
    args = _unpack_parser().parse_args(argv)
    color = supports_color()
    try:
        if args.inspect:
            manifest = inspect_bundle(args.bundle)
            print(
                json.dumps(manifest, indent=2, sort_keys=True) if args.json else format_manifest(manifest, color=color)
            )
            return 0

        if args.verify:
            problems = verify_bundle(args.bundle)
            if args.json:
                print(json.dumps({"bundle": str(args.bundle), "ok": not problems, "problems": problems}, indent=2))
            elif problems:
                print(colorize(f"{args.bundle}: FAILED", "red", enabled=color), file=sys.stderr)
                for problem in problems:
                    print(f"  {problem}", file=sys.stderr)
            else:
                print(colorize(f"{args.bundle}: ok", "green", enabled=color))
            return 1 if problems else 0

        written = extract_bundle(
            args.bundle,
            args.directory,
            verify=not args.no_verify,
            overwrite=args.force,
        )
    except ToolError as err:
        print(f"dalaran-unpack: {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"extracted": [str(path) for path in written]}, indent=2))
    else:
        for path in written:
            print(path)
    return 0
