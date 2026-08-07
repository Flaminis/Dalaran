#!/usr/bin/env python3

"""
Update the version of the `dalaran_notebook`.

This includes:
- the `dalaran_notebook` package itself
- the dependency in the `dalaran_py/pyproject.toml` file.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import semver
import tomlkit


def run(
    cmd: str,
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> None:
    print(f"{cwd or ''}> {cmd}")
    subprocess.check_output(cmd.split(), cwd=cwd, env=env)


def set_dalaran_notebook_version(pyproject_path: Path, version: str) -> None:
    pyproject: dict[str, Any] = tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))
    pyproject["project"]["version"] = version
    pyproject_path.write_text(tomlkit.dumps(pyproject), encoding="utf-8")


def set_dependency_version(pyproject_path: Path, version: str) -> None:
    pyproject: dict[str, Any] = tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))

    for extra in ("notebook", "all"):
        deps = pyproject["project"]["optional-dependencies"][extra]
        new_deps = [dep for dep in deps if not dep.startswith("dalaran-notebook")]
        new_deps.append(f"dalaran-notebook=={version}")
        pyproject["project"]["optional-dependencies"][extra] = sorted(new_deps)

    pyproject_path.write_text(tomlkit.dumps(pyproject), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update dalaran notebook dependency version")
    parser.add_argument("VERSION", help="Version to use")
    args = parser.parse_args()

    # check that the version is valid
    try:
        semver.VersionInfo.parse(args.VERSION)
    except ValueError:
        print(f"Invalid semver version: '{args.VERSION}'", file=sys.stderr, flush=True)
        sys.exit(1)

    project_path = Path(__file__).parent.parent.parent.absolute()

    # update the version in dalaran_notebook
    set_dalaran_notebook_version(project_path / "dalaran_notebook" / "pyproject.toml", args.VERSION)

    # update the dependency in dalaran_py/pyproject.toml
    pyproject_path = project_path / "dalaran_py" / "pyproject.toml"
    set_dependency_version(pyproject_path, args.VERSION)


if __name__ == "__main__":
    main()
