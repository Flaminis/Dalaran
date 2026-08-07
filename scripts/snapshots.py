"""
View or clean failed kittest snapshot tests.

Usage:
```
pixi run snapshot --help
```
"""

from __future__ import annotations

import argparse
from pathlib import Path
from sys import stderr
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

import dalaran as dl
import dalaran.blueprint as dlb

if TYPE_CHECKING:
    from collections.abc import Iterator

CRATES_DIR = Path(__file__).parent.parent / "crates"


def find_failed_snapshot_tests(package: str | None) -> Iterator[tuple[Path, Path, Path]]:
    for diff_path in CRATES_DIR.rglob("**/*.diff.png"):
        if package is not None:
            if not any(package == str(part) for part in diff_path.parts):
                continue

        original_path = diff_path.parent / diff_path.name.replace(".diff.png", ".png")
        new_path = diff_path.parent / diff_path.name.replace(".diff.png", ".new.png")

        if original_path.exists() and new_path.exists():
            yield original_path, new_path, diff_path


def blueprint(path: Path) -> dlb.Blueprint:
    test_name = path.stem
    crate_name = path.relative_to(CRATES_DIR).parts[1]

    return dlb.Blueprint(
        dlb.Tabs(
            dlb.Horizontal(
                dlb.Spatial2DView(origin="original", name="Original"),
                dlb.Spatial2DView(origin="new", name="New"),
                dlb.Spatial2DView(origin="diff", name="Diff"),
                name="Side-by-side",
            ),
            dlb.Tabs(
                dlb.Spatial2DView(origin="original", name="Original"),
                dlb.Spatial2DView(origin="new", name="New"),
                dlb.Spatial2DView(origin="diff", name="Diff"),
            ),
            dlb.Tabs(
                dlb.Vertical(
                    dlb.Spatial2DView(
                        contents=["/original", "/new"],
                        name="Overlay (opacity)",
                        overrides={"/new": dl.Image(opacity=0.5)},
                    ),
                    name='NOTE: Select the "new" entity visualizer and play with the "Opacity" component',
                ),
                name="Overlay (tab)",
            ),
            name=f"{crate_name}/{test_name}",
        ),
        dlb.TimePanel(expanded=False),
    )


def log_failed_snapshot_tests(original_path: Path, new_path: Path, diff_path: Path, args: argparse.Namespace) -> None:
    recording = dl.RecordingStream(f"dalaran_example_{original_path.stem}")

    with recording:
        default_blueprint = blueprint(original_path)

        if args.stdout:
            dl.stdout(default_blueprint=default_blueprint)
        elif args.serve:
            connect_to = dl.serve_grpc(default_blueprint=default_blueprint)
            dl.serve_web_viewer(open_browser=True, connect_to=connect_to)
        elif args.connect:
            dl.connect_grpc(args.addr, default_blueprint=default_blueprint)
        elif args.save is not None:
            dl.save(args.save, default_blueprint=default_blueprint)
        elif not args.headless:
            dl.spawn(default_blueprint=default_blueprint)

        dl.log("original", dl.Image(np.array(Image.open(original_path))), static=True)
        dl.log("new", dl.Image(np.array(Image.open(new_path))), static=True)
        dl.log("diff", dl.Image(np.array(Image.open(diff_path))), static=True)

        dl.log(
            "doc/tabs",
            dl.TextDocument(
                "### Click on one of the tabs below to show the Original/New/Diff images.",
                media_type="text/markdown",
            ),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Logs all failed snapshot tests for comparison in dalaran")
    parser.add_argument("-p", "--package", type=str, help="Only consider the provided package")
    parser.add_argument("--clean", action="store_true", help="Clean snapshot files instead of displaying them")
    dl.script_add_args(parser)

    args = parser.parse_args()

    none_found = True
    for original_path, new_path, diff_path in find_failed_snapshot_tests(args.package):
        none_found = False

        if args.clean:
            print(f"Removing {new_path}", file=stderr)
            new_path.unlink(missing_ok=True)
            print(f"Removing {diff_path}", file=stderr)
            diff_path.unlink(missing_ok=True)
        else:
            log_failed_snapshot_tests(original_path, new_path, diff_path, args)

    if none_found:
        print("No failed snapshot found", file=stderr)


if __name__ == "__main__":
    main()
