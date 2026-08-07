---
title: dalaran-doctor
order: 1
---

`dalaran-doctor` diagnoses a Dalaran installation and prints a report. Run it first whenever
something does not behave the way you expect: it checks the handful of things that are wrong in
almost every bug report.

```sh
dalaran-doctor
```

```txt
dalaran-doctor  (dalaran-sdk 0.36.0)

[ok  ] python       Python 3.11.9 in a virtual environment
[ok  ] sdk          dalaran-sdk 0.36.0
[FAIL] viewer       viewer (dalaran-cli 0.35.1) and dalaran-sdk (0.36.0) are from incompatible releases
       hint: Recordings are only guaranteed to load within a minor release; upgrade whichever side is older.
[ok  ] graphics     wgpu should use the vulkan backend
[warn] display      headless session: neither DISPLAY nor WAYLAND_DISPLAY is set
       hint: Use `dl.serve_grpc()` and the web viewer, or log to a .dlr file instead of spawning a window.
[ok  ] ros2         ROS 2 jazzy is sourced
[ok  ] environment  2 DALARAN_* variable(s) set, all recognized
[warn] endpoint     nothing is listening on 127.0.0.1:9876
       hint: Start a viewer with `dalaran --serve`, or pass --endpoint to check a different address.

1 check(s) failed: viewer
```

## What is checked

| Check | What it tells you |
|-------|-------------------|
| `python` | Interpreter version, path, and whether you are inside a virtual environment. |
| `sdk` | The installed `dalaran-sdk` version and whether its native bindings and dependencies import. |
| `viewer` | Whether the `dalaran` binary is on `PATH`, and whether its version is compatible with the SDK. |
| `graphics` | The wgpu backend that will be used, plus GPU/driver details where we can get them. |
| `display` | Whether this is an X11, Wayland or headless session. |
| `ros2` | Whether a ROS 2 distribution is installed and sourced. |
| `environment` | `DALARAN_*` variables, typos in them, and stale `RERUN_*` leftovers. |
| `endpoint` | Whether a gRPC endpoint accepts connections. |

## Statuses and exit code

Each check reports `ok`, `warn`, `fail` or `skip`. The process exits with `1` if and only if at
least one check **failed**, i.e. something is actually broken. Warnings describe a setup that may
be intentional (a headless server, no ROS 2 installed, no viewer running yet) and keep the exit
code at `0`, so `dalaran-doctor` is safe to put in CI.

## Options

| Flag | Meaning |
|------|---------|
| `--json` | Emit a machine-readable report instead of the text one. |
| `--verbose`, `-v` | Also print the details collected by each check. |
| `--endpoint URL` | Probe a specific gRPC endpoint (default `dalaran+http://127.0.0.1:9876/proxy`). |
| `--no-network` | Skip the endpoint probe entirely. |

## JSON output

```sh
dalaran-doctor --json --no-network
```

```json
{
  "schema_version": 1,
  "status": "warn",
  "dalaran_version": "0.36.0",
  "checks": [
    {
      "name": "python",
      "status": "ok",
      "summary": "Python 3.11.9 in a virtual environment",
      "details": { "version": "3.11.9", "virtual_env": true },
      "hint": null
    }
  ]
}
```

`schema_version` is bumped whenever the shape of the report changes, so a CI job can pin it.

## From Python

```python
from dalaran.tools.doctor import run_checks

report = run_checks(skip_network=True)
broken = [check for check in report["checks"] if check["status"] == "fail"]
```
