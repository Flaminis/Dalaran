"""Development helper for dalaran-sdk editable installs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_repo_root() -> Path | None:
    """Find the dalaran repo root directory."""
    # Try PIXI_PROJECT_ROOT first (set when running under pixi)
    pixi_root = os.environ.get("PIXI_PROJECT_ROOT")
    if pixi_root:
        return Path(pixi_root)

    # Otherwise walk up from the venv (sys.prefix) to find the repo root. For the
    # workspace .venv this is the immediate parent; for an isolated example's .venv
    # (examples/python/<name>/.venv) it is several levels up. The repo root is the
    # first ancestor that holds both `pixi.toml` and the `dalaran_py` source tree.
    for parent in Path(sys.prefix).parents:
        if (parent / "pixi.toml").is_file() and (parent / "dalaran_py").is_dir():
            return parent

    return None


def init() -> None:
    """
    Sitecustomize entrypoint that sets DALARAN_CLI_PATH.

    This runs early during Python startup (before .pth files),
    ensuring the env var is set before dalaran_sdk is imported.
    """
    # Don't override if already set
    if "DALARAN_CLI_PATH" in os.environ:
        return

    repo_root = _find_repo_root()
    if repo_root is None:
        return

    cli_path = repo_root / "target" / "debug" / "dalaran"

    if cli_path.exists():
        os.environ["DALARAN_CLI_PATH"] = str(cli_path)
