"""Script to manage artifacts stored in Google Cloud Storage."""

from __future__ import annotations

import argparse
import os
import stat
import tarfile
from pathlib import Path

from google.cloud import storage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--commit-sha", required=True, help="Which sha are we fetching artifacts for")
    parser.add_argument(
        "--artifact", choices=["dalaran-cli", "dalaran-cli-macos-app"], help="Which artifact are we fetching"
    )
    parser.add_argument(
        "--platform",
        choices=[
            "linux-arm64",
            "linux-x64",
            "macos-arm64",
            "windows-x64",
        ],
    )
    parser.add_argument("--dest", required=True, help="Where to save the artifact to")

    args = parser.parse_args()

    # dalaran-cli-macos-app fetches the macOS .app bundle (tarball) and extracts it into --dest.
    if args.artifact == "dalaran-cli-macos-app":
        if args.platform != "macos-arm64":
            raise SystemExit("--artifact dalaran-cli-macos-app is only valid with --platform macos-arm64")
        bucket_path = f"commit/{args.commit_sha}/dalaran-cli/{args.platform}/Dalaran.app.tar.gz"
        print(f"Fetching artifact from {bucket_path} to {args.dest}")
        gcs = storage.Client()
        bucket = gcs.bucket("dalaran-builds")
        artifact = bucket.blob(bucket_path)
        os.makedirs(args.dest, exist_ok=True)
        tarball = Path(args.dest) / "Dalaran.app.tar.gz"
        with open(tarball, "wb") as f:
            artifact.download_to_file(f)
        with tarfile.open(tarball, "r:gz") as tar:
            # `filter="data"` rejects absolute paths and `..` components in members.
            tar.extractall(args.dest, filter="data")
        tarball.unlink()
        return

    artifact_names: dict[tuple[str, str], str] = {}
    artifact_names["dalaran-cli", "linux-arm64"] = "dalaran"
    artifact_names["dalaran-cli", "linux-x64"] = "dalaran"
    artifact_names["dalaran-cli", "macos-arm64"] = "dalaran"
    artifact_names["dalaran-cli", "windows-x64"] = "dalaran.exe"

    artifact_name = artifact_names[args.artifact, args.platform]

    bucket_path = f"commit/{args.commit_sha}/{args.artifact}/{args.platform}/{artifact_name}"
    print(f"Fetching artifact from {bucket_path} to {args.dest}")

    gcs = storage.Client()
    bucket = gcs.bucket("dalaran-builds")
    artifact = bucket.blob(bucket_path)

    os.makedirs(args.dest, exist_ok=True)

    filename = os.path.join(args.dest, artifact_name)

    with open(filename, "wb") as f:
        artifact.download_to_file(f)

    file = Path(filename)
    file.chmod(file.stat().st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    main()
