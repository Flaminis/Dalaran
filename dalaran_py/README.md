# The Dalaran Python SDK

Use the Dalaran SDK to record data like images, tensors, point clouds, and text. Data is streamed to the Dalaran Viewer for live visualization or to file for later use.

<p align="center">
  <img width="800" alt="Dalaran Viewer" src="https://github.com/rerun-io/rerun/assets/2624717/c4900538-fc3a-43b8-841a-8d226e7b5a2e">
</p>

## Install

```sh
pip3 install dalaran-sdk
```

ℹ️ Note:
The Python module is called `dalaran`, while the package published on PyPI is `dalaran-sdk`.

For other SDK languages see [Installing Dalaran](https://www.dalaran.dev/docs/overview/installing-dalaran/viewer).

We also provide a [Jupyter widget](https://pypi.org/project/dalaran-notebook/) for interactive data visualization in Jupyter notebooks:
```sh
pip3 install dalaran-sdk[notebook]
```

## Example
```py
import dalaran as dl
import numpy as np

dl.init("dalaran_example_app", spawn=True)

positions = np.vstack([xyz.ravel() for xyz in np.mgrid[3 * [slice(-5, 5, 10j)]]]).T
colors = np.vstack([rgb.ravel() for rgb in np.mgrid[3 * [slice(0, 255, 10j)]]]).astype(np.uint8).T

dl.log("points3d", dl.Points3D(positions, colors=colors))
```

## Resources
* [Examples](https://www.dalaran.dev/examples)
* [Python API docs](https://ref.dalaran.dev/docs/python)
* [Quick start](https://www.dalaran.dev/docs/getting-started/data-in/python)
* [Tutorial](https://www.dalaran.dev/docs/getting-started/data-in/python)
* [Troubleshooting](https://www.dalaran.dev/docs/overview/installing-dalaran/troubleshooting)
* [Discord Server](https://discord.com/invite/Gcm8BbTaAj)

## Logging and viewing in different processes

You can run the Viewer and logger in different processes.

In one terminal, start up a Viewer with a server that the SDK can connect to:
```sh
python3 -m dalaran
```

In a second terminal, run the example with the `--connect` option:
```sh
python3 examples/python/plots/plots.py --connect
```
Note that SDK and Viewer can run on different machines!


# Building Dalaran from source

We use [`pixi`](https://pixi.sh/) for managing dev-tool versioning, download and task running. See [here](https://pixi.sh/latest/#installation) for installation instructions.

```sh
pixi run py-build
```
This builds the SDK for Python (use `pixi run py-build --release` for a release build).

You can then run examples via uv:
```sh
pixi run uv run examples/python/minimal/minimal.py
```

To build a wheel instead for manual install use:
```sh
pixi run py-build-wheel
```

Refer to [BUILD.md](../BUILD.md) for details on the various different build options of the Dalaran Viewer and SDKs for all target languages.


# Installing a pre-release

Prebuilt dev wheels from head of main are available at <https://github.com/rerun-io/rerun/releases/tag/prerelease>.

While we try to keep the main branch usable at all times, it may be unstable occasionally. Use at your own risk.


# Running Python unit tests
```sh
pixi run py-test
```

If you run into a problem, run `rm -rf .pixi .venv` and try again.

# Running specific Python unit tests
```sh
pixi run py-build && pixi run uvpy -m pytest dalaran_py/tests/unit/test_tensor.py
```

# Profiling the Python SDK

Set `DALARAN_PUFFIN=1` to spawn a [`puffin_viewer`](https://github.com/EmbarkStudios/puffin) attached to the SDK on startup. The Rust side of the SDK then streams scopes (anything wrapped in `dl_tracing::profile_function!` / `profile_scope!`) to the viewer for the lifetime of the process.

```sh
DALARAN_PUFFIN=1 pixi run uvpy your_script.py
```

Save a recording from the viewer for offline analysis (use the `investigate-puffin` skill in `.claude/skills/`).
