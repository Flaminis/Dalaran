#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import multiprocessing
import os
import shutil
import subprocess
import tempfile

from google.cloud import storage


def run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    cwd: str | None = None,
) -> None:
    print(f"> {subprocess.list2cmdline(args)}")
    result = subprocess.run(args, env=env, cwd=cwd, timeout=timeout, check=False, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"{subprocess.list2cmdline(args)} failed with exit-code {result.returncode}. Output:\n{result.stdout}\n{result.stderr}"
    )


def download_dalaran_c(target_dir: str, git_hash: str, platform_filter: str | None = None) -> None:
    logging.info("Downloading dalaran_c…")

    gcs = storage.Client("dalaran-open")
    bucket = gcs.bucket("dalaran-builds")

    os.mkdir(target_dir)

    # See reusable_build_and_upload_dalaran_c.yml for available libraries.
    # See dalaran_cpp_sdk/CMakeLists.txt for library names.
    for src, dst in [
        ("linux-arm64/libdalaran_c.a", "libdalaran_c__linux_arm64.a"),
        ("linux-x64/libdalaran_c.a", "libdalaran_c__linux_x64.a"),
        ("macos-arm64/libdalaran_c.a", "libdalaran_c__macos_arm64.a"),
        ("windows-x64/dalaran_c.lib", "dalaran_c__win_x64.lib"),
    ]:
        if platform_filter is not None and src.startswith(platform_filter) is False:
            continue

        blob = bucket.get_blob(f"commit/{git_hash}/dalaran_c/{src}")
        if blob is None:
            raise RuntimeError(f"Blob not found: commit/{git_hash}/dalaran_c/{src}")
        with open(f"{target_dir}/{dst}", "wb") as f:
            logging.info(f"Copying {blob.path} to {target_dir}/{dst}")
            blob.download_to_file(f)


def upload_dalaran_cpp_sdk(dalaran_zip: str, git_hash: str) -> None:
    logging.info("Uploading to gcloud…")

    gcs = storage.Client("dalaran-open")
    bucket = gcs.bucket("dalaran-builds")
    destination = bucket.blob(f"commit/{git_hash}/dalaran_cpp_sdk.zip")
    destination.content_type = "application/zip"
    destination.upload_from_filename(dalaran_zip)
    logging.info(f"Uploaded to https://build.dalaran.dev/commit/{git_hash}/dalaran_cpp_sdk.zip")


def test_fetch_content(git_hash: str) -> None:
    logging.info("Testing uploaded artifact…")

    logging.info("-> Testing without installing dalaran…")
    with tempfile.TemporaryDirectory() as testdir:
        shutil.copytree("examples/cpp/minimal/", testdir, dirs_exist_ok=True)
        run(["cmake", f"-DDALARAN_CPP_URL=https://build.dalaran.dev/commit/{git_hash}/dalaran_cpp_sdk.zip", "."], cwd=testdir)
        run(["cmake", "--build", ".", "--parallel", str(multiprocessing.cpu_count())], cwd=testdir)


def test_install(dalaran_zip: str) -> None:
    logging.info("Testing using an install artifact…")

    with tempfile.TemporaryDirectory() as testdir:
        # unpacking the dalaran_cpp_sdk.zip and installing it to a local directory.
        shutil.unpack_archive(dalaran_zip, f"{testdir}")
        os.makedirs(f"{testdir}/build")
        os.makedirs(f"{testdir}/install")
        os.makedirs(f"{testdir}/example")
        run(  # configure
            ["cmake", "-B", "../build", "."],
            cwd=f"{testdir}/dalaran_cpp_sdk/",
        )
        run(  # build
            ["cmake", "--build", "../build", "--target", "dalaran_sdk", "--parallel", str(multiprocessing.cpu_count())],
            cwd=f"{testdir}/dalaran_cpp_sdk/",
        )
        run(  # install
            ["cmake", "--install", "../build", "--prefix", "../install"],
            cwd=f"{testdir}/dalaran_cpp_sdk/",
        )

        # Using the install.
        shutil.copytree("examples/cpp/minimal/", f"{testdir}/example", dirs_exist_ok=True)
        run(["cmake", "-DDALARAN_FIND_PACKAGE=ON", "-DCMAKE_PREFIX_PATH=../install", "."], cwd=f"{testdir}/example")
        run(["cmake", "--build", ".", "--parallel", str(multiprocessing.cpu_count())], cwd=f"{testdir}/example")


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Bundle and upload dalaran_cpp_sdk. Assumes dalaran_c already built & uploaded.",
    )
    parser.add_argument(
        "--git-hash",
        required=True,
        type=str,
        help="Git hash for which we're downloading dalaran_c and uploading dalaran_cpp_sdk.",
    )
    parser.add_argument(
        "--platform-filter",
        type=str,
        default=None,
        help="If set, only the specified platform will be fetched for dalaran_c.",
    )
    parser.add_argument("--no-upload", help="If true, don't upload dalaran_cpp_sdk.", action="store_true")
    parser.add_argument("--skip-test", help="If true, don't test dalaran_cpp_sdk after upload.", action="store_true")
    parser.add_argument(
        "--local-path",
        required=False,
        default=None,
        type=str,
        help="If set, dalaran_cpp_sdk bundle will be written on disk.",
    )
    args = parser.parse_args()

    git_hash = args.git_hash[:7]

    with tempfile.TemporaryDirectory() as scratch_dir:
        package_name = "dalaran_cpp_sdk"
        package_dir = scratch_dir + "/" + package_name
        os.mkdir(package_dir)

        download_dalaran_c(package_dir + "/lib", git_hash, args.platform_filter)

        logging.info("Copying files…")
        shutil.copytree(
            src="dalaran_cpp/",
            dst=package_dir + "/",
            ignore=shutil.ignore_patterns("tests"),
            dirs_exist_ok=True,
        )

        logging.info("Copying LICENSE files…")
        shutil.copy(src="LICENSE-APACHE", dst=package_dir + "/")
        shutil.copy(src="LICENSE-MIT", dst=package_dir + "/")

        logging.info(f"Packaging {package_dir}.zip…")
        dalaran_zip = shutil.make_archive(
            scratch_dir + "/" + package_name,
            "zip",
            root_dir=scratch_dir,
            base_dir=package_name,
        )

        if args.local_path is not None:
            logging.info(f"Copying dalaran_cpp_sdk bundle to local path from '{dalaran_zip}' to '{args.local_path}'")
            shutil.copy(dalaran_zip, args.local_path)

        if args.skip_test is not True:
            test_install(dalaran_zip)

        if args.no_upload is not True:
            upload_dalaran_cpp_sdk(dalaran_zip, git_hash)

    if args.skip_test is not True and args.no_upload is not True:
        test_fetch_content(git_hash)


if __name__ == "__main__":
    main()
