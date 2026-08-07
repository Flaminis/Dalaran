"""
`dalaran-init`: scaffold a ready-to-run Dalaran project.

Starting a new robotics visualization usually means copying an old script and
deleting the parts you do not need. `dalaran-init` instead generates a small but
complete project that logs real data, comes with a blueprint, a README and a
`.gitignore`, and can be run immediately.

Templates
---------
`python`
    A standalone script plus a `pyproject.toml`.
`ros2`
    An `ament_python` package with a node that bridges ROS 2 topics to Dalaran.
`cpp`
    A CMake project using the C++ SDK.
`rust`
    A Cargo binary crate using the Rust SDK.

Example
-------
```python
from dalaran.tools.scaffold import create_project

created = create_project("./my_robot", template="python")
print([path.name for path in created])
```

"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ._common import ToolError, colorize, sdk_version, supports_color

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "TEMPLATES",
    "create_project",
    "main",
    "render_template",
]

TEMPLATES = ("python", "ros2", "cpp", "rust")
"""Names accepted by `--template`."""

_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 _.-]*$")


def _context(project_name: str) -> dict[str, str]:
    package = re.sub(r"[^A-Za-z0-9_]+", "_", project_name).strip("_").lower() or "dalaran_project"
    if package[0].isdigit():
        package = f"p_{package}"
    version = sdk_version()
    # Templates pin a released minor, because a local `+dev` version is not on PyPI.
    match = re.match(r"^(\d+)\.(\d+)", version)
    pinned = f"{match.group(1)}.{match.group(2)}" if match else "0.36"
    return {
        "project": project_name,
        "package": package,
        "app_id": package,
        "sdk_version": version,
        "sdk_pin": pinned,
    }


def render_template(text: str, context: dict[str, str]) -> str:
    """
    Substitute `{{key}}` placeholders in a template body.

    A dedicated mini-syntax is used instead of `str.format` because the C++ and
    Rust templates are full of braces of their own.

    Parameters
    ----------
    text:
        Template body.
    context:
        Mapping of placeholder name to replacement.

    Returns
    -------
    str
        The rendered text.

    Raises
    ------
    ToolError
        If a placeholder has no value in `context`.

    Example
    -------
    ```python
    from dalaran.tools.scaffold import render_template

    assert render_template("hello {{project}}", {"project": "robot"}) == "hello robot"
    ```

    """

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise ToolError(f"unknown template placeholder {{{{{key}}}}}")
        return context[key]

    return re.sub(r"\{\{(\w+)\}\}", replace, text)


_GITIGNORE = """\
# Dalaran artifacts
*.dlr
*.dlrpack

# Python
__pycache__/
*.py[cod]
.venv/
dist/
build/

# Rust
target/

# Editors
.vscode/
.idea/
"""

_BLUEPRINT_PY = '''\
#!/usr/bin/env python3
"""Build the blueprint for {{project}} and save it as `overview.dbl`."""

from __future__ import annotations

import dalaran.blueprint as dlb

APPLICATION_ID = "{{app_id}}"


def make_blueprint() -> dlb.Blueprint:
    """Two side-by-side views: the 3D scene, and the scalars logged next to it."""
    return dlb.Blueprint(
        dlb.Horizontal(
            dlb.Spatial3DView(origin="/world", name="Scene"),
            dlb.TimeSeriesView(origin="/telemetry", name="Telemetry"),
            column_shares=[2, 1],
        ),
        collapse_panels=True,
    )


def main() -> None:
    make_blueprint().save(APPLICATION_ID, "overview.dbl")
    print("wrote overview.dbl")


if __name__ == "__main__":
    main()
'''

_PYTHON_MAIN = '''\
#!/usr/bin/env python3
"""{{project}}: a minimal but real Dalaran logging script."""

from __future__ import annotations

import argparse

import numpy as np

import dalaran as dl
from blueprint import APPLICATION_ID, make_blueprint


def main() -> None:
    parser = argparse.ArgumentParser(description="Log a rotating point cloud and its telemetry.")
    parser.add_argument("--save", metavar="PATH", default=None, help="write a .dlr recording instead of spawning a viewer")
    parser.add_argument("--steps", type=int, default=120, help="number of simulated time steps")
    args = parser.parse_args()

    dl.init(APPLICATION_ID, spawn=args.save is None, default_blueprint=make_blueprint())
    if args.save is not None:
        dl.save(args.save)

    rng = np.random.default_rng(42)
    positions = rng.normal(scale=2.0, size=(512, 3))
    colors = np.clip(128.0 + positions * 40.0, 0.0, 255.0).astype(np.uint8)

    for step in range(args.steps):
        dl.set_time("step", sequence=step)

        angle = step * 0.05
        rotation = np.array([
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ])
        rotated = positions @ rotation.T

        dl.log("/world/points", dl.Points3D(rotated, colors=colors, radii=0.05))
        dl.log("/telemetry/height", dl.Scalars(float(rotated[:, 2].mean())))


if __name__ == "__main__":
    main()
'''

_PYTHON_PYPROJECT = """\
[build-system]
build-backend = "setuptools.build_meta"
requires = ["setuptools>=68"]

[project]
name = "{{package}}"
version = "0.1.0"
description = "A Dalaran visualization project"
requires-python = ">=3.10"
dependencies = [
  "dalaran-sdk>={{sdk_pin}}",
  "numpy>=2",
]
"""

_PYTHON_README = """\
# {{project}}

A Dalaran project scaffolded with `dalaran-init --template python`.

## Run it

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e .
python main.py                  # spawns the viewer
python main.py --save run.dlr   # writes a recording instead
```

## Blueprint

`blueprint.py` defines the default layout used by `main.py`. Write it out as a
standalone blueprint file with:

```sh
python blueprint.py             # writes overview.dbl
```

## Share a recording

```sh
dalaran-pack {{package}}.dlrpack run.dlr --blueprint overview.dbl --tag demo
```

## Something not working?

```sh
dalaran-doctor
```
"""

_ROS2_NODE = '''\
#!/usr/bin/env python3
"""A ROS 2 node that mirrors odometry and laser scans into Dalaran."""

from __future__ import annotations

import numpy as np
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

import dalaran as dl

APPLICATION_ID = "{{app_id}}"


class DalaranBridge(Node):
    """Subscribes to a couple of standard topics and logs them to Dalaran."""

    def __init__(self) -> None:
        super().__init__("dalaran_bridge")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("scan_topic", "/scan")

        odom_topic = self.get_parameter("odom_topic").get_parameter_value().string_value
        scan_topic = self.get_parameter("scan_topic").get_parameter_value().string_value

        self.create_subscription(Odometry, odom_topic, self.on_odometry, 10)
        self.create_subscription(LaserScan, scan_topic, self.on_scan, 10)
        self.get_logger().info(f"bridging {odom_topic} and {scan_topic} into Dalaran")

    def set_time_from(self, stamp) -> None:
        dl.set_time("ros_time", timestamp=stamp.sec + stamp.nanosec * 1e-9)

    def on_odometry(self, msg: Odometry) -> None:
        self.set_time_from(msg.header.stamp)
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation
        dl.log(
            "/world/robot",
            dl.Transform3D(
                translation=[position.x, position.y, position.z],
                quaternion=[orientation.x, orientation.y, orientation.z, orientation.w],
            ),
        )
        dl.log("/telemetry/speed", dl.Scalars(float(msg.twist.twist.linear.x)))

    def on_scan(self, msg: LaserScan) -> None:
        self.set_time_from(msg.header.stamp)
        ranges = np.asarray(msg.ranges, dtype=np.float32)
        angles = msg.angle_min + np.arange(ranges.size, dtype=np.float32) * msg.angle_increment
        finite = np.isfinite(ranges) & (ranges >= msg.range_min) & (ranges <= msg.range_max)
        points = np.column_stack([
            ranges[finite] * np.cos(angles[finite]),
            ranges[finite] * np.sin(angles[finite]),
            np.zeros(int(finite.sum()), dtype=np.float32),
        ])
        dl.log("/world/robot/scan", dl.Points3D(points, radii=0.02))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    dl.init(APPLICATION_ID, spawn=True)
    node = DalaranBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
'''

_ROS2_SETUP_PY = '''\
"""ament_python packaging for {{project}}."""

from __future__ import annotations

from setuptools import setup

package_name = "{{package}}"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "dalaran-sdk>={{sdk_pin}}"],
    zip_safe=True,
    maintainer="you",
    maintainer_email="you@example.com",
    description="Bridges ROS 2 topics into Dalaran",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "dalaran_bridge = {{package}}.dalaran_bridge:main",
        ],
    },
)
'''

_ROS2_PACKAGE_XML = """\
<?xml version="1.0"?>
<package format="3">
  <name>{{package}}</name>
  <version>0.1.0</version>
  <description>Bridges ROS 2 topics into Dalaran</description>
  <maintainer email="you@example.com">you</maintainer>
  <license>Apache-2.0</license>

  <exec_depend>rclpy</exec_depend>
  <exec_depend>nav_msgs</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
"""

_ROS2_README = """\
# {{project}}

A ROS 2 (`ament_python`) package scaffolded with `dalaran-init --template ros2`.
It subscribes to `/odom` and `/scan` and logs both into Dalaran.

## Build and run

```sh
source /opt/ros/$ROS_DISTRO/setup.bash
pip install "dalaran-sdk>={{sdk_pin}}"
colcon build --packages-select {{package}}
source install/setup.bash
ros2 run {{package}} dalaran_bridge --ros-args -p scan_topic:=/scan
```

Replay a bag in another terminal to see data show up:

```sh
ros2 bag play my_bag
```

## Blueprint

```sh
python blueprint.py             # writes overview.dbl
```
"""

_CPP_MAIN = """\
// {{project}}: a minimal but real Dalaran C++ logging program.

#include <cmath>
#include <cstdint>
#include <vector>

#include <dalaran.hpp>

int main() {
    const auto rec = dalaran::RecordingStream("{{app_id}}");
    rec.spawn().exit_on_failure();

    std::vector<dalaran::Position3D> points;
    std::vector<dalaran::Color> colors;
    points.reserve(64 * 64);
    colors.reserve(64 * 64);

    for (int y = 0; y < 64; ++y) {
        for (int x = 0; x < 64; ++x) {
            const float fx = static_cast<float>(x) * 0.1f - 3.2f;
            const float fy = static_cast<float>(y) * 0.1f - 3.2f;
            points.emplace_back(fx, fy, std::sin(fx) * std::cos(fy));
            colors.emplace_back(
                static_cast<uint8_t>(x * 4), static_cast<uint8_t>(y * 4), static_cast<uint8_t>(128)
            );
        }
    }

    for (int step = 0; step < 120; ++step) {
        rec.set_time_sequence("step", step);

        const float phase = static_cast<float>(step) * 0.05f;
        std::vector<dalaran::Position3D> wave;
        wave.reserve(points.size());
        for (const auto& point : points) {
            wave.emplace_back(point.xyz.x(), point.xyz.y(), std::sin(point.xyz.x() + phase));
        }

        rec.log("/world/surface", dalaran::Points3D(wave).with_colors(colors).with_radii({0.02f}));
        rec.log("/telemetry/phase", dalaran::Scalars(static_cast<double>(phase)));
    }
}
"""

_CPP_CMAKE = """\
cmake_minimum_required(VERSION 3.16...3.27)
project({{package}} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Fetch the Dalaran C++ SDK. Configure with -DDALARAN_FIND_PACKAGE=ON to use a preinstalled one.
option(DALARAN_FIND_PACKAGE "Use a preinstalled dalaran_sdk instead of downloading it" OFF)

if(DALARAN_FIND_PACKAGE)
    find_package(dalaran_sdk REQUIRED)
else()
    include(FetchContent)
    set(DALARAN_CPP_URL
        "https://github.com/Flaminis/Dalaran/releases/latest/download/dalaran_cpp_sdk.zip"
        CACHE STRING "URL of the dalaran_cpp SDK zip")
    FetchContent_Declare(dalaran_sdk URL ${DALARAN_CPP_URL})
    FetchContent_MakeAvailable(dalaran_sdk)
endif()

add_executable({{package}} src/main.cpp)
target_link_libraries({{package}} PRIVATE dalaran_sdk)
"""

_CPP_README = """\
# {{project}}

A C++ project scaffolded with `dalaran-init --template cpp`.

## Build and run

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/{{package}}
```

The first configure downloads the Dalaran C++ SDK. If you already have it
installed, configure with `-DDALARAN_FIND_PACKAGE=ON` instead.

## Blueprint

```sh
python blueprint.py             # writes overview.dbl
```
"""

_RUST_MAIN = """\
//! {{project}}: a minimal but real Dalaran logging program.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("{{app_id}}").spawn()?;

    let points: Vec<(f32, f32, f32)> = (0..64)
        .flat_map(|y| {
            (0..64).map(move |x| {
                let fx = x as f32 * 0.1 - 3.2;
                let fy = y as f32 * 0.1 - 3.2;
                (fx, fy, fx.sin() * fy.cos())
            })
        })
        .collect();

    let colors: Vec<dalaran::Color> = points
        .iter()
        .map(|(x, y, _)| {
            dalaran::Color::from_rgb(((x + 3.2) * 40.0) as u8, ((y + 3.2) * 40.0) as u8, 128)
        })
        .collect();

    for step in 0..120 {
        rec.set_time_sequence("step", step);

        let phase = step as f32 * 0.05;
        let wave: Vec<(f32, f32, f32)> = points
            .iter()
            .map(|(x, y, _)| (*x, *y, (x + phase).sin()))
            .collect();

        rec.log(
            "/world/surface",
            &dalaran::Points3D::new(wave)
                .with_colors(colors.clone())
                .with_radii([0.02]),
        )?;
        rec.log("/telemetry/phase", &dalaran::Scalars::single(phase as f64))?;
    }

    Ok(())
}
"""

_RUST_CARGO = """\
[package]
name = "{{package}}"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"
publish = false

[dependencies]
dalaran = "{{sdk_pin}}"
"""

_RUST_README = """\
# {{project}}

A Rust project scaffolded with `dalaran-init --template rust`.

## Build and run

```sh
cargo run --release
```

## Blueprint

```sh
python blueprint.py             # writes overview.dbl
```
"""

_TEMPLATE_FILES: dict[str, dict[str, str]] = {
    "python": {
        "main.py": _PYTHON_MAIN,
        "blueprint.py": _BLUEPRINT_PY,
        "pyproject.toml": _PYTHON_PYPROJECT,
        "README.md": _PYTHON_README,
        ".gitignore": _GITIGNORE,
    },
    "ros2": {
        "{{package}}/__init__.py": '"""ROS 2 to Dalaran bridge for {{project}}."""\n',
        "{{package}}/dalaran_bridge.py": _ROS2_NODE,
        "resource/{{package}}": "",
        "setup.py": _ROS2_SETUP_PY,
        "package.xml": _ROS2_PACKAGE_XML,
        "blueprint.py": _BLUEPRINT_PY,
        "README.md": _ROS2_README,
        ".gitignore": _GITIGNORE,
    },
    "cpp": {
        "src/main.cpp": _CPP_MAIN,
        "CMakeLists.txt": _CPP_CMAKE,
        "blueprint.py": _BLUEPRINT_PY,
        "README.md": _CPP_README,
        ".gitignore": _GITIGNORE,
    },
    "rust": {
        "src/main.rs": _RUST_MAIN,
        "Cargo.toml": _RUST_CARGO,
        "blueprint.py": _BLUEPRINT_PY,
        "README.md": _RUST_README,
        ".gitignore": _GITIGNORE,
    },
}

_TEMPLATE_HELP = {
    "python": "standalone Python script with a pyproject.toml",
    "ros2": "ament_python package bridging /odom and /scan into Dalaran",
    "cpp": "CMake project using the C++ SDK",
    "rust": "Cargo binary crate using the Rust SDK",
}

_NEXT_STEPS = {
    "python": ("pip install -e .", "python main.py"),
    "ros2": ("colcon build --packages-select {{package}}", "ros2 run {{package}} dalaran_bridge"),
    "cpp": ("cmake -B build -DCMAKE_BUILD_TYPE=Release", "cmake --build build -j", "./build/{{package}}"),
    "rust": ("cargo run --release",),
}

_EXECUTABLE = frozenset({"main.py", "blueprint.py", "dalaran_bridge.py"})


def create_project(
    destination: str | Path,
    *,
    template: str = "python",
    name: str | None = None,
    force: bool = False,
) -> list[Path]:
    """
    Generate a project from a template and return the files that were written.

    Parameters
    ----------
    destination:
        Directory to create. Its name is used as the project name unless `name`
        is given.
    template:
        One of `TEMPLATES`, i.e. `"python"`, `"ros2"`, `"cpp"` or `"rust"`.
    name:
        Override the project name.
    force:
        Write into a directory that already contains files.

    Returns
    -------
    list of pathlib.Path
        The generated files, in a stable order.

    Raises
    ------
    ToolError
        On an unknown template, an unusable project name, or a non-empty
        destination without `force`.

    Example
    -------
    ```python
    from dalaran.tools.scaffold import create_project

    created = create_project("/tmp/my_robot", template="rust")
    assert any(path.name == "Cargo.toml" for path in created)
    ```

    """
    if template not in _TEMPLATE_FILES:
        raise ToolError(f"unknown template {template!r}; pick one of: {', '.join(TEMPLATES)}")

    root = Path(destination)
    project_name = name if name is not None else root.name
    if not _IDENTIFIER_RE.match(project_name):
        raise ToolError(
            f"{project_name!r} is not a usable project name; "
            "start with a letter and use letters, digits, spaces, '_', '-' or '.'",
        )
    if root.exists() and any(root.iterdir()) and not force:
        raise ToolError(f"{root} is not empty (pass --force to scaffold into it anyway)")

    context = _context(project_name)
    written: list[Path] = []
    for raw_path, body in sorted(_TEMPLATE_FILES[template].items()):
        target = root / render_template(raw_path, context)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_template(body, context), encoding="utf-8")
        if target.name in _EXECUTABLE:
            target.chmod(0o755)
        written.append(target)
    return written


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dalaran-init",
        description="Scaffold a ready-to-run Dalaran project.",
    )
    parser.add_argument("destination", nargs="?", help="directory to create")
    parser.add_argument("--template", "-t", default="python", choices=TEMPLATES, help="which template to use")
    parser.add_argument("--name", default=None, help="project name (defaults to the directory name)")
    parser.add_argument("--force", action="store_true", help="scaffold into a non-empty directory")
    parser.add_argument("--list", action="store_true", help="list the available templates and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Entry point of the `dalaran-init` console script.

    Example
    -------
    ```python
    from dalaran.tools.scaffold import main

    raise SystemExit(main(["my_robot", "--template", "python"]))
    ```

    """
    parser = _parser()
    args = parser.parse_args(argv)
    color = supports_color()

    if args.list:
        for template in TEMPLATES:
            print(f"  {colorize(template, 'cyan', enabled=color)}  {_TEMPLATE_HELP[template]}")
        return 0

    if args.destination is None:
        parser.error("the following arguments are required: destination")

    try:
        written = create_project(args.destination, template=args.template, name=args.name, force=args.force)
    except ToolError as err:
        print(f"dalaran-init: {err}", file=sys.stderr)
        return 1

    root = Path(args.destination)
    print(colorize(f"Created a {args.template} project in {root}", "green", enabled=color))
    for path in written:
        print(f"  {path.relative_to(root)}")

    context = _context(args.name if args.name is not None else root.name)
    print("\nNext steps:")
    print(f"  cd {root}")
    for step in _NEXT_STEPS[args.template]:
        print(f"  {render_template(step, context)}")
    return 0
