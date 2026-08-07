#!/usr/bin/env python3

"""
Build and upload dalaran_notebook wheels to GCS.

IMPORTANT: dalaran_js must be built beforehand, otherwise this script will fail. Use `pixi run js-build-base`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import zipfile

from google.cloud.storage import Bucket
from google.cloud.storage import Client as Gcs


def run(
    cmd: str,
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> None:
    print(f"{cwd or ''}> {cmd}")
    subprocess.check_output(cmd.split(), cwd=cwd, env=env)


def build_and_upload(bucket: Bucket, gcs_dir: str) -> str:
    dist = "dist/"

    # Build into `dist`
    run(
        f"hatch build -t wheel ../{dist}",
        cwd="dalaran_notebook",
    )

    pkg = os.listdir(dist)[0]
    wheel = f"{dist}/{pkg}"

    # Upload to GCS
    print("Uploading to GCS…")
    bucket.blob(f"{gcs_dir}/{pkg}").upload_from_filename(wheel)

    return wheel


def publish_notebook_asset(bucket: Bucket, gcs_dir: str, wheel: str) -> None:
    """Extract widget.js and dl_viewer_bg.wasm from the notebook wheel and upload to the web viewer bucket."""

    with zipfile.ZipFile(wheel, "r") as archive:
        archive.extract("dalaran_notebook/static/widget.js", "extracted")
        archive.extract("dalaran_notebook/static/dl_viewer_bg.wasm", "extracted")

    for filename in ["widget.js", "dl_viewer_bg.wasm"]:
        local_path = f"extracted/dalaran_notebook/static/{filename}"
        blob = bucket.blob(f"{gcs_dir}/{filename}")
        print(f"Uploading {local_path} to gs://{bucket.name}/{blob.name}")
        blob.upload_from_filename(local_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and upload dalaran_notebook wheels to GCS")
    parser.add_argument("--dir", required=True, help="Upload the wheel to the given directory in GCS")
    parser.add_argument(
        "--notebook-dir",
        required=False,
        help="Upload notebook assets (widget.js, dl_viewer_bg.wasm) to the given directory in the web viewer bucket",
    )
    args = parser.parse_args()

    gcs = Gcs("dalaran-open")

    wheel = build_and_upload(
        gcs.bucket("dalaran-builds"),
        args.dir,
    )

    if args.notebook_dir:
        publish_notebook_asset(
            gcs.bucket("dalaran-web-viewer"),
            args.notebook_dir,
            wheel,
        )


if __name__ == "__main__":
    main()
