"""Shared helpers for the Dalaran command line tools (colors, hashing, versions)."""

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

__all__ = [
    "BLUEPRINT_SUFFIX",
    "BUNDLE_SUFFIX",
    "RECORDING_SUFFIX",
    "ToolError",
    "colorize",
    "human_bytes",
    "parse_version",
    "sdk_version",
    "sha256_file",
    "supports_color",
    "versions_compatible",
]

RECORDING_SUFFIX = ".dlr"
"""File extension of a Dalaran recording."""

BLUEPRINT_SUFFIX = ".dbl"
"""File extension of a Dalaran blueprint."""

BUNDLE_SUFFIX = ".dlrpack"
"""File extension of a portable Dalaran bundle."""

_ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}


class ToolError(RuntimeError):
    """Raised for user-facing errors; the CLI wrappers turn these into a clean message."""


def supports_color(stream: object | None = None) -> bool:
    """
    Whether ANSI escape codes should be emitted on `stream`.

    Honors the `NO_COLOR` and `FORCE_COLOR` conventions before falling back to a
    TTY check, so output stays readable when piped into a file or a CI log.

    Example
    -------
    ```python
    from dalaran.tools._common import supports_color

    print(supports_color(open("/dev/null", "w")))  # False
    ```

    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    stream = stream if stream is not None else sys.stdout
    isatty = getattr(stream, "isatty", None)
    return bool(isatty and isatty())


def colorize(text: str, color: str, *, enabled: bool = True) -> str:
    """
    Wrap `text` in an ANSI color, or return it unchanged when `enabled` is false.

    Example
    -------
    ```python
    from dalaran.tools._common import colorize

    assert colorize("ok", "green", enabled=False) == "ok"
    ```

    """
    if not enabled or color not in _ANSI:
        return text
    return f"{_ANSI[color]}{text}{_ANSI['reset']}"


def human_bytes(size: int) -> str:
    """
    Format a byte count using binary units.

    Example
    -------
    ```python
    from dalaran.tools._common import human_bytes

    assert human_bytes(2048) == "2.0 KiB"
    ```

    """
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024.0 or unit == "TiB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    raise AssertionError("unreachable")


def sha256_file(path: str | Path, *, chunk_size: int = 1 << 20) -> str:
    """
    Compute the hex-encoded SHA-256 digest of a file, streaming it in chunks.

    Example
    -------
    ```python
    from pathlib import Path
    from dalaran.tools._common import sha256_file

    Path("hello.txt").write_text("hello", encoding="utf-8")
    print(sha256_file("hello.txt"))
    ```

    """
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while True:
            block = file.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sdk_version() -> str:
    """
    Best-effort version of the installed `dalaran-sdk`.

    Importing `dalaran` pulls in the compiled bindings, which is exactly the
    thing that may be broken when the user runs `dalaran-doctor`. We therefore
    ask the package metadata first, and only then fall back to parsing the
    source tree we are running from. Returns `"unknown"` when both fail.

    Example
    -------
    ```python
    from dalaran.tools._common import sdk_version

    print(sdk_version())
    ```

    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("dalaran-sdk")
        except PackageNotFoundError:
            pass
    except ImportError:  # pragma: no cover - importlib.metadata is stdlib since 3.8
        pass

    init_py = Path(__file__).resolve().parent.parent / "__init__.py"
    try:
        source = init_py.read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.MULTILINE)
    return match.group(1) if match else "unknown"


def parse_version(text: str) -> tuple[int, int, int] | None:
    """
    Extract a `(major, minor, patch)` triple from a free-form version string.

    Viewer binaries print things like `dalaran-cli 0.36.0-alpha.1+dev`, so we
    only look for the first dotted numeric triple.

    Example
    -------
    ```python
    from dalaran.tools._common import parse_version

    assert parse_version("dalaran-cli 0.36.0-alpha.1+dev") == (0, 36, 0)
    ```

    """
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def versions_compatible(lhs: str, rhs: str) -> bool | None:
    """
    Whether an SDK and a viewer version can talk to each other.

    Dalaran keeps wire compatibility within a minor release, so we compare
    `major.minor`. Returns `None` when either version cannot be parsed.

    Example
    -------
    ```python
    from dalaran.tools._common import versions_compatible

    assert versions_compatible("0.36.0", "0.36.2")
    assert not versions_compatible("0.36.0", "0.37.0")
    ```

    """
    left = parse_version(lhs)
    right = parse_version(rhs)
    if left is None or right is None:
        return None
    return left[:2] == right[:2]
