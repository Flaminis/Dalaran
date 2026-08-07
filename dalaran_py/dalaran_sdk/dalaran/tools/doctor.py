"""
`dalaran-doctor`: diagnose a Dalaran installation.

Most "Dalaran does not work" reports come down to a handful of environment
problems: a viewer binary from a different release, a headless machine without a
display, a GPU driver that wgpu cannot use, a firewalled gRPC port, or a stale
`RERUN_*` environment variable left over from a migration. This tool checks all
of that in one go and prints a report, with `--json` for CI.

Exit codes
----------
`0`
    Everything is fine, or only warnings were raised.
`1`
    At least one check failed, i.e. something is actually broken.

Example
-------
```python
from dalaran.tools.doctor import run_checks

report = run_checks()
print(report["status"], [check["name"] for check in report["checks"]])
```

"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from ._common import ToolError, colorize, sdk_version, supports_color, versions_compatible

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "DEFAULT_ENDPOINT",
    "REPORT_SCHEMA_VERSION",
    "STATUSES",
    "main",
    "run_checks",
]

REPORT_SCHEMA_VERSION = 1
"""Version of the `--json` report schema."""

DEFAULT_ENDPOINT = "dalaran+http://127.0.0.1:9876/proxy"
"""Endpoint probed when `--endpoint` is not given; this is what `dalaran --serve` binds by default."""

STATUSES = ("ok", "warn", "fail", "skip")
"""Possible values of a check's `status` field, in increasing order of severity (`skip` aside)."""

KNOWN_ENV_VARS = {
    "DALARAN_CHUNK_MAX_ROWS_IF_UNSORTED": "maximum number of rows in an unsorted chunk",
    "DALARAN_FLUSH_NUM_BYTES": "byte threshold before the SDK flushes a chunk",
    "DALARAN_FLUSH_NUM_ROWS": "row threshold before the SDK flushes a chunk",
    "DALARAN_FLUSH_TICK_SECS": "time threshold before the SDK flushes a chunk",
    "DALARAN_MAPBOX_ACCESS_TOKEN": "token used by map views",
    "DALARAN_PANIC_ON_WARN": "turn warnings into panics (debugging only)",
    "DALARAN_STRICT": "turn recoverable SDK errors into hard errors",
    "DALARAN_TELEMETRY_ENDPOINT": "OTLP endpoint for client-side tracing",
    "DALARAN_TRACK_ALLOCATIONS": "expensive allocation tracking (debugging only)",
    "DALARAN_WORKSPACE": "path to the Dalaran source workspace (development only)",
}
"""Environment variables the SDK and viewer understand, with a one-line explanation."""

_NUMERIC_ENV_VARS = (
    "DALARAN_CHUNK_MAX_ROWS_IF_UNSORTED",
    "DALARAN_FLUSH_NUM_BYTES",
    "DALARAN_FLUSH_NUM_ROWS",
    "DALARAN_FLUSH_TICK_SECS",
)

_WGPU_BACKENDS = {
    "Darwin": "metal",
    "Windows": "dx12",
    "Linux": "vulkan",
}

_SEVERITY = {"skip": 0, "ok": 1, "warn": 2, "fail": 3}


def _check(
    name: str,
    status: str,
    summary: str,
    *,
    details: dict[str, Any] | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    return {
        "name": name,
        "status": status,
        "summary": summary,
        "details": details or {},
        "hint": hint,
    }


def _run(command: Sequence[str], *, timeout: float = 10.0) -> tuple[int, str]:
    """Run a command and return `(returncode, combined output)`; never raises."""
    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as err:
        return (-1, str(err))
    return (completed.returncode, (completed.stdout + completed.stderr).strip())


def check_python() -> dict[str, Any]:
    """Report the interpreter, and whether it is inside a virtual environment."""
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix) or bool(os.environ.get("VIRTUAL_ENV"))
    details = {
        "version": platform.python_version(),
        "executable": sys.executable,
        "implementation": platform.python_implementation(),
        "virtual_env": in_venv,
        "platform": platform.platform(),
    }
    if not in_venv:
        return _check(
            "python",
            "warn",
            f"Python {platform.python_version()} (not in a virtual environment)",
            details=details,
            hint="Installing into the system interpreter often leads to version conflicts.",
        )
    return _check("python", "ok", f"Python {platform.python_version()} in a virtual environment", details=details)


def check_sdk() -> dict[str, Any]:
    """Report the SDK version and whether its native bindings and hard dependencies import."""
    details: dict[str, Any] = {"version": sdk_version()}
    missing: list[str] = []
    for module in ("dalaran_bindings", "numpy", "pyarrow"):
        try:
            __import__(module)
        except ImportError as err:
            details[module] = f"missing: {err}"
            missing.append(module)
        else:
            details[module] = "ok"

    if "dalaran_bindings" in missing:
        return _check(
            "sdk",
            "fail",
            f"dalaran-sdk {details['version']} is installed but its native bindings do not import",
            details=details,
            hint="Reinstall with `pip install --force-reinstall dalaran-sdk`, or build them with `pixi run py-build`.",
        )
    if missing:
        return _check(
            "sdk",
            "fail",
            f"dalaran-sdk {details['version']} is missing dependencies: {', '.join(missing)}",
            details=details,
            hint="Reinstall with `pip install dalaran-sdk` to pull in the required dependencies.",
        )
    return _check("sdk", "ok", f"dalaran-sdk {details['version']}", details=details)


def check_viewer() -> dict[str, Any]:
    """Locate the `dalaran` viewer binary and compare its version with the SDK."""
    binary = shutil.which("dalaran")
    if binary is None:
        return _check(
            "viewer",
            "warn",
            "the `dalaran` viewer binary is not on PATH",
            details={"path": None},
            hint="Install it with `pip install dalaran-sdk` (it ships the viewer) or `cargo install dalaran-cli`.",
        )

    code, output = _run([binary, "--version"])
    details: dict[str, Any] = {"path": binary, "output": output}
    if code != 0:
        return _check(
            "viewer",
            "fail",
            "the `dalaran` viewer binary could not be executed",
            details=details,
            hint="Run `dalaran --version` by hand to see the underlying error.",
        )

    sdk = sdk_version()
    compatible = versions_compatible(sdk, output)
    details["sdk_version"] = sdk
    details["compatible"] = compatible
    if compatible is False:
        return _check(
            "viewer",
            "fail",
            f"viewer ({output}) and dalaran-sdk ({sdk}) are from incompatible releases",
            details=details,
            hint="Recordings are only guaranteed to load within a minor release; upgrade whichever side is older.",
        )
    if compatible is None:
        return _check(
            "viewer",
            "warn",
            f"could not compare viewer and SDK versions ({output!r} vs {sdk!r})",
            details=details,
        )
    return _check("viewer", "ok", f"viewer {output} matches the SDK", details=details)


def check_graphics() -> dict[str, Any]:
    """Guess whether wgpu will find a usable adapter on this machine."""
    system = platform.system()
    backend = os.environ.get("WGPU_BACKEND") or _WGPU_BACKENDS.get(system, "unknown")
    details: dict[str, Any] = {"system": system, "wgpu_backend": backend}

    gpu_tool = shutil.which("nvidia-smi")
    if gpu_tool is not None:
        code, output = _run([gpu_tool, "--query-gpu=name,driver_version", "--format=csv,noheader"])
        if code == 0 and output:
            details["nvidia"] = output.splitlines()

    if system == "Linux":
        render_nodes = (
            sorted(str(node) for node in Path("/dev/dri").glob("render*")) if Path("/dev/dri").is_dir() else []
        )
        details["dri_render_nodes"] = render_nodes
        if not render_nodes and "nvidia" not in details:
            return _check(
                "graphics",
                "warn",
                "no GPU render node found under /dev/dri",
                details=details,
                hint="The viewer will fall back to software rendering; inside a container pass `--device /dev/dri`.",
            )
    elif system not in ("Darwin", "Windows"):
        return _check("graphics", "warn", f"unrecognized platform {system!r}", details=details)

    return _check("graphics", "ok", f"wgpu should use the {backend} backend", details=details)


def check_display() -> dict[str, Any]:
    """Detect headless sessions and report the windowing system in use."""
    system = platform.system()
    details: dict[str, Any] = {
        "system": system,
        "DISPLAY": os.environ.get("DISPLAY"),
        "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY"),
        "ssh_session": bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY")),
    }
    if system != "Linux":
        return _check("display", "ok", f"{system} always provides a native window server", details=details)

    if details["WAYLAND_DISPLAY"]:
        details["session_type"] = "wayland"
        return _check("display", "ok", "Wayland session detected", details=details)
    if details["DISPLAY"]:
        details["session_type"] = "x11"
        return _check("display", "ok", "X11 session detected", details=details)

    details["session_type"] = "headless"
    return _check(
        "display",
        "warn",
        "headless session: neither DISPLAY nor WAYLAND_DISPLAY is set",
        details=details,
        hint="Use `dl.serve_grpc()` and the web viewer, or log to a .dlr file instead of spawning a window.",
    )


def check_ros2() -> dict[str, Any]:
    """Report whether a ROS 2 distribution is sourced or at least installed."""
    distro = os.environ.get("ROS_DISTRO")
    ros2_cli = shutil.which("ros2")
    installed = sorted(str(path.name) for path in Path("/opt/ros").iterdir()) if Path("/opt/ros").is_dir() else []
    details = {"ROS_DISTRO": distro, "ros2_cli": ros2_cli, "installed_distros": installed}

    if distro and ros2_cli:
        return _check("ros2", "ok", f"ROS 2 {distro} is sourced", details=details)
    if installed:
        return _check(
            "ros2",
            "warn",
            f"ROS 2 is installed ({', '.join(installed)}) but not sourced in this shell",
            details=details,
            hint=f"Run `source /opt/ros/{installed[0]}/setup.bash` before using the ROS 2 bridge.",
        )
    return _check("ros2", "skip", "no ROS 2 installation found (only needed for the ROS 2 bridge)", details=details)


def check_environment() -> dict[str, Any]:
    """Validate `DALARAN_*` variables and flag leftovers from other tools."""
    dalaran_vars = {key: value for key, value in os.environ.items() if key.startswith("DALARAN_")}
    stale_vars = sorted(key for key in os.environ if key.startswith("RERUN_"))
    unknown = sorted(key for key in dalaran_vars if key not in KNOWN_ENV_VARS)
    bad_numbers = sorted(key for key in _NUMERIC_ENV_VARS if key in dalaran_vars and not _is_number(dalaran_vars[key]))
    details = {
        "dalaran_vars": dict(sorted(dalaran_vars.items())),
        "unknown_vars": unknown,
        "stale_rerun_vars": stale_vars,
        "malformed_vars": bad_numbers,
    }

    if bad_numbers:
        return _check(
            "environment",
            "fail",
            f"malformed numeric environment variable(s): {', '.join(bad_numbers)}",
            details=details,
            hint="These are parsed as numbers; a bad value makes the SDK fall back to defaults or refuse to start.",
        )
    if stale_vars:
        return _check(
            "environment",
            "warn",
            f"leftover RERUN_* variable(s) that Dalaran ignores: {', '.join(stale_vars)}",
            details=details,
            hint="Rename them to their DALARAN_* equivalent, or unset them.",
        )
    if unknown:
        return _check(
            "environment",
            "warn",
            f"unrecognized DALARAN_* variable(s): {', '.join(unknown)}",
            details=details,
            hint="Check for typos; unknown variables are silently ignored.",
        )
    return _check(
        "environment", "ok", f"{len(dalaran_vars)} DALARAN_* variable(s) set, all recognized", details=details
    )


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def check_endpoint(endpoint: str = DEFAULT_ENDPOINT, *, timeout: float = 2.0) -> dict[str, Any]:
    """Try to open a TCP connection to a `dalaran://`-style gRPC endpoint."""
    host, port = _split_endpoint(endpoint)
    details: dict[str, Any] = {"endpoint": endpoint, "host": host, "port": port, "timeout_seconds": timeout}
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as err:
        details["error"] = str(err)
        return _check(
            "endpoint",
            "warn",
            f"nothing is listening on {host}:{port}",
            details=details,
            hint="Start a viewer with `dalaran --serve`, or pass --endpoint to check a different address.",
        )
    return _check("endpoint", "ok", f"reachable at {host}:{port}", details=details)


def _split_endpoint(endpoint: str) -> tuple[str, int]:
    """
    Split a `dalaran://host:port` (or `host:port`) endpoint into its host and port.

    Example
    -------
    ```python
    from dalaran.tools.doctor import _split_endpoint

    assert _split_endpoint("dalaran+http://127.0.0.1:9876/proxy") == ("127.0.0.1", 9876)
    ```

    """
    text = endpoint if "//" in endpoint else f"//{endpoint}"
    parsed = urlparse(text)
    host = parsed.hostname
    if host is None:
        raise ToolError(f"{endpoint!r}: could not determine a host name")
    try:
        port = parsed.port
    except ValueError as err:
        raise ToolError(f"{endpoint!r}: invalid port ({err})") from err
    return (host, port or 9876)


def run_checks(*, endpoint: str = DEFAULT_ENDPOINT, skip_network: bool = False) -> dict[str, Any]:
    """
    Run every diagnostic and return a JSON-serializable report.

    Parameters
    ----------
    endpoint:
        gRPC endpoint to probe, e.g. `"dalaran+http://127.0.0.1:9876/proxy"`.
    skip_network:
        Skip the endpoint probe, which is useful on machines without a network.

    Returns
    -------
    dict
        Keys: `schema_version`, `status` (worst status seen), `dalaran_version`
        and `checks` (a list of per-check dicts).

    Example
    -------
    ```python
    from dalaran.tools.doctor import run_checks

    report = run_checks(skip_network=True)
    assert report["status"] in {"ok", "warn", "fail"}
    ```

    """
    checks = [
        check_python(),
        check_sdk(),
        check_viewer(),
        check_graphics(),
        check_display(),
        check_ros2(),
        check_environment(),
    ]
    if skip_network:
        checks.append(_check("endpoint", "skip", "network probe skipped", details={"endpoint": endpoint}))
    else:
        checks.append(check_endpoint(endpoint))

    worst = max((check["status"] for check in checks), key=lambda status: _SEVERITY[status])
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "ok" if worst == "skip" else worst,
        "dalaran_version": sdk_version(),
        "checks": checks,
    }


_STATUS_STYLE = {
    "ok": ("ok  ", "green"),
    "warn": ("warn", "yellow"),
    "fail": ("FAIL", "red"),
    "skip": ("skip", "dim"),
}


def format_report(report: dict[str, Any], *, color: bool = False, verbose: bool = False) -> str:
    """
    Render a report from [run_checks][dalaran.tools.doctor.run_checks] as text.

    Example
    -------
    ```python
    from dalaran.tools.doctor import format_report, run_checks

    print(format_report(run_checks(skip_network=True)))
    ```

    """
    lines = [colorize(f"dalaran-doctor  (dalaran-sdk {report['dalaran_version']})", "bold", enabled=color), ""]
    for check in report["checks"]:
        label, style = _STATUS_STYLE[check["status"]]
        lines.append(f"[{colorize(label, style, enabled=color)}] {check['name']:<12} {check['summary']}")
        if check["hint"] and check["status"] in ("warn", "fail"):
            lines.append(f"       {colorize('hint: ' + check['hint'], 'dim', enabled=color)}")
        if verbose:
            for key, value in check["details"].items():
                lines.append(f"       {key}: {value}")

    failures = [check["name"] for check in report["checks"] if check["status"] == "fail"]
    lines.append("")
    if failures:
        lines.append(colorize(f"{len(failures)} check(s) failed: {', '.join(failures)}", "red", enabled=color))
    else:
        lines.append(colorize("no failures", "green", enabled=color))
    return "\n".join(lines)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dalaran-doctor",
        description="Diagnose a Dalaran installation and print a report.",
    )
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report for CI")
    parser.add_argument("--verbose", "-v", action="store_true", help="print the details of every check")
    parser.add_argument(
        "--endpoint", default=DEFAULT_ENDPOINT, help=f"gRPC endpoint to probe (default: {DEFAULT_ENDPOINT})"
    )
    parser.add_argument("--no-network", action="store_true", help="skip the endpoint probe")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Entry point of the `dalaran-doctor` console script.

    Example
    -------
    ```python
    from dalaran.tools.doctor import main

    raise SystemExit(main(["--json", "--no-network"]))
    ```

    """
    args = _parser().parse_args(argv)
    try:
        report = run_checks(endpoint=args.endpoint, skip_network=args.no_network)
    except ToolError as err:
        print(f"dalaran-doctor: {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_report(report, color=supports_color(), verbose=args.verbose))
    return 1 if report["status"] == "fail" else 0
