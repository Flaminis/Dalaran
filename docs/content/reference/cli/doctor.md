---
title: doctor
order: 1
---

Dalaran ships two diagnostics, and you should reach for whichever one still runs:

* `dalaran doctor` is a subcommand of the viewer binary. It knows what the binary was built
  from, asks wgpu directly which graphics adapters exist, and can validate a recording. It needs
  no Python at all.
* `dalaran-doctor` is a Python console script that ships with `dalaran-sdk`. It knows about your
  interpreter, your virtual environment, and whether the SDK and the viewer are from compatible
  releases.

They overlap on purpose. Both print the same kind of report, use the same statuses, and emit the
same `--json` schema, so a CI job can consume either. Run both if you are unsure which half of
your installation is broken.

## `dalaran doctor`

```sh
dalaran doctor
```

```txt
dalaran doctor  (dalaran 0.1.0)

[ok  ] build        dalaran 0.1.0
[FAIL] graphics     no usable graphics adapter for the enabled backend(s): vulkan, gl
       hint: The viewer cannot open a window without one. On a headless or containerized machine, install a software rasterizer (Mesa's `lavapipe`), or use `dalaran --serve-web` and view in a browser instead.
[warn] environment  leftover RERUN_* variable(s) that Dalaran ignores: RERUN_STRICT
       hint: Rename them, or unset them: RERUN_STRICT -> DALARAN_STRICT.
[warn] display      headless session: neither DISPLAY nor WAYLAND_DISPLAY is set
       hint: Use `dalaran --serve-web` and the web viewer, or `--save recording.dlr`, instead of spawning a window.
[ok  ] ros2         ROS 2 jazzy is sourced
[skip] endpoint     no --endpoint given, so no connection was attempted

1 check(s) failed: graphics
```

### What is checked

| Check | What it tells you |
|-------|-------------------|
| `build` | Version, git hash, build target, enabled features, and whether this is an unoptimized debug build. |
| `graphics` | Every wgpu adapter on the machine, and which one the viewer would pick. This is the usual cause of a black screen. |
| `environment` | `DALARAN_*` variables, typos in them, values that do not parse, and stale `RERUN_*` leftovers. Secrets are redacted. |
| `display` | Whether this is an X11, Wayland or headless session. |
| `ros2` | `ROS_DISTRO`, `ROS_VERSION`, `RMW_IMPLEMENTATION` and `ROS_DOMAIN_ID`. |
| `recording` | One per file argument: framing, decodability, message and chunk counts, application id. |
| `endpoint` | Whether the gRPC endpoint given with `--endpoint` accepts connections. |

### Validating a recording

Pass one or more files to check that they are recordings the viewer can actually open:

```sh
dalaran doctor session.dlr
```

```txt
[ok  ] recording    session.dlr: 1204 message(s), 1198 chunk(s), app id my_robot
```

The file is decoded with the same code the viewer uses, so anything this accepts will load. Legacy
Rerun `.rrd` and `.rbl` files are read natively and labelled as such. Four failure modes are
distinguished, because from the outside they look identical:

* the file is not a recording at all, e.g. a renamed MCAP — use [`dalaran convert`](../cli.md);
* it was written by a version whose encoding is no longer supported;
* it decodes but has no footer, meaning the producer died before the stream was flushed — the data
  that is there still loads, but the tail is gone;
* it is well-formed and empty, meaning nothing was ever logged into it.

### Options

| Flag | Meaning |
|------|---------|
| `--json` | Emit a machine-readable report instead of the text one. |
| `--verbose`, `-v` | Also print the details collected by each check. |
| `--endpoint URL` | Probe a gRPC endpoint, e.g. `dalaran+http://127.0.0.1:9876/proxy`. Nothing is probed without it. |
| `--no-network` | Never touch the network; the endpoint probe reports `skip`. |

## `dalaran-doctor`

```sh
dalaran-doctor
```

```txt
dalaran-doctor  (dalaran-sdk 0.1.0)

[ok  ] python       Python 3.11.9 in a virtual environment
[ok  ] sdk          dalaran-sdk 0.1.0
[FAIL] viewer       viewer (dalaran-cli 0.0.9) and dalaran-sdk (0.1.0) are from incompatible releases
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

### What is checked

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

Unlike `dalaran doctor`, the Python script probes `dalaran+http://127.0.0.1:9876/proxy` by
default; pass `--no-network` to stop it.

## Statuses and exit code

Each check reports `ok`, `warn`, `fail` or `skip`. Both tools exit with `1` if and only if at
least one check **failed**, i.e. something is actually broken. Warnings describe a setup that may
be intentional (a headless server, no ROS 2 installed, no viewer running yet) and keep the exit
code at `0`, so both are safe to put in CI.

## JSON output

```sh
dalaran doctor --json --no-network
```

```json
{
  "schema_version": 1,
  "status": "warn",
  "dalaran_version": "0.1.0",
  "checks": [
    {
      "name": "build",
      "status": "ok",
      "summary": "dalaran 0.1.0",
      "details": { "target_triple": "x86_64-unknown-linux-gnu", "debug_build": false },
      "hint": null
    }
  ]
}
```

`schema_version` is shared by both tools and bumped whenever the shape of the report changes, so a
CI job can pin it. `status` is the worst status of any check, `details` is free-form per check,
and `hint` is `null` unless there is something to do about it.

## From Python

```python
from dalaran.tools.doctor import run_checks

report = run_checks(skip_network=True)
broken = [check for check in report["checks"] if check["status"] == "fail"]
```
