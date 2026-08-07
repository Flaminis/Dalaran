#!/usr/bin/env python3

"""
Updates the version information for Python & C SDK.

This includes:
- Python
    - `dalaran.__version__`
    - `dalaran.__version_info__`
- C/C++
    - `#define DALARAN_SDK_HEADER_VERSION`
    - `#define DALARAN_SDK_HEADER_VERSION_MAJOR`
    - `#define DALARAN_SDK_HEADER_VERSION_MINOR`
    - `#define DALARAN_SDK_HEADER_VERSION_PATCH`
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import semver


def update_python_line(line: str, version_line: str, version_info_line: str) -> str:
    if line.startswith("__version__"):
        return version_line
    if line.startswith("__version_info__"):
        return version_info_line
    return line


def set_dalaran_py_version(init_path: Path, version: semver.VersionInfo) -> None:
    version_line = f'__version__ = "{version}"\n'
    version_info_items = [str(item) for item in (version.major, version.minor, version.patch)]
    if version.prerelease is not None:
        version_info_items.append(f'"{version.prerelease}"')
    else:
        version_info_items.append("None")

    version_info_line = f"__version_info__ = ({', '.join(version_info_items)})\n"

    with init_path.open(encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [update_python_line(line, version_line, version_info_line) for line in lines]

    if new_lines != lines:
        with init_path.open("w", encoding="utf-8") as f:
            f.writelines(new_lines)
    else:
        print(f"Version already set to {version} in {init_path}")


def update_c_line(
    line: str,
    version_line: str,
    version_line_major: str,
    version_line_minor: str,
    version_line_patch: str,
) -> str:
    if line.startswith("#define DALARAN_SDK_HEADER_VERSION_MAJOR"):
        return version_line_major
    elif line.startswith("#define DALARAN_SDK_HEADER_VERSION_MINOR"):
        return version_line_minor
    elif line.startswith("#define DALARAN_SDK_HEADER_VERSION_PATCH"):
        return version_line_patch
    elif line.startswith("#define DALARAN_SDK_HEADER_VERSION"):
        return version_line

    return line


def set_dalaran_c_version(init_path: Path, version: semver.VersionInfo) -> None:
    version_line = f'#define DALARAN_SDK_HEADER_VERSION "{version}"\n'
    version_line_major = f"#define DALARAN_SDK_HEADER_VERSION_MAJOR {version.major}\n"
    version_line_minor = f"#define DALARAN_SDK_HEADER_VERSION_MINOR {version.minor}\n"
    version_line_patch = f"#define DALARAN_SDK_HEADER_VERSION_PATCH {version.patch}\n"

    with init_path.open(encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [
        update_c_line(line, version_line, version_line_major, version_line_minor, version_line_patch) for line in lines
    ]
    if new_lines != lines:
        with init_path.open("w", encoding="utf-8") as f:
            f.writelines(new_lines)
    else:
        print(f"Version already set to {version} in {init_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update dalaran_py __version__ variable & dalaran_c version defines.")
    parser.add_argument("VERSION", help="Version to use")
    args = parser.parse_args()

    # check that the version is valid
    try:
        semver.VersionInfo.parse(args.VERSION)
    except ValueError:
        print(f"Invalid semver version: {args.VERSION}", file=sys.stderr, flush=True)
        sys.exit(1)

    project_path = Path(__file__).parent.parent.parent.absolute()

    sem_version = semver.VersionInfo.parse(args.VERSION)
    set_dalaran_py_version(project_path / "dalaran_py" / "dalaran_sdk" / "dalaran" / "__init__.py", sem_version)
    set_dalaran_c_version(project_path / "dalaran_cpp" / "src" / "dalaran" / "c" / "sdk_info.h", sem_version)


if __name__ == "__main__":
    main()
