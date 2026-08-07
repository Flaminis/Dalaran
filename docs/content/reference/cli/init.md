---
title: dalaran-init
order: 2
---

`dalaran-init` scaffolds a complete, runnable Dalaran project so you can go from an empty
directory to a live visualization in about a minute.

```sh
dalaran-init my_robot --template python
cd my_robot
pip install -e .
python main.py
```

## Templates

| Template | What you get |
|----------|--------------|
| `python` | A script that logs a rotating point cloud plus telemetry, a `pyproject.toml`, and a blueprint. |
| `ros2` | An `ament_python` package with a node that bridges `/odom` and `/scan` into Dalaran. |
| `cpp` | A CMake project that fetches the C++ SDK and logs an animated surface. |
| `rust` | A Cargo binary crate doing the same with the Rust SDK. |

List them at any time:

```sh
dalaran-init --list
```

Every template also contains a `README.md` with the exact build and run commands, a `blueprint.py`
that writes a standalone `overview.dbl`, and a `.gitignore` that ignores `.dlr` recordings and
`.dlrpack` bundles.

## Options

| Flag | Meaning |
|------|---------|
| `--template`, `-t` | One of `python`, `ros2`, `cpp`, `rust` (default: `python`). |
| `--name` | Project name; defaults to the destination directory name. |
| `--force` | Scaffold into a directory that already contains files. |
| `--list` | Print the available templates and exit. |

The project name is sanitized into a valid package identifier, so
`dalaran-init "My Robot"` produces a package called `my_robot` while keeping the pretty name in
the README.

## From Python

```python
from dalaran.tools.scaffold import create_project

created = create_project("./my_robot", template="rust")
```
