#!/usr/bin/env python3

"""
Run some of our python examples, piping their log stream to the dalaran process.

This is an end-to-end test for testing:
* Our Python API
* LogMsg encoding/decoding
* Arrow encoding/decoding
* gRPC connection
* Data store ingestion
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path

PORT = 9752


def main() -> None:
    parser = argparse.ArgumentParser(description="Runs end-to-end tests of select python example.")
    parser.add_argument("--no-build", action="store_true", help="Skip building dalaran-sdk")
    parser.add_argument("--no-install", action="store_true", help="Skip installing the examples")

    if parser.parse_args().no_build:
        print("Skipping building dalaran-sdk - assuming it is already built and up-to-date!")
    else:
        build_env = os.environ.copy()
        if "RUST_LOG" in build_env:
            del build_env["RUST_LOG"]  # The user likely only meant it for the actual tests; not the setup

        print("----------------------------------------------------------")
        print("Building dalaran-sdk…")
        start_time = time.time()
        subprocess.Popen(["pixi", "run", "py-build"], env=build_env).wait()
        elapsed = time.time() - start_time
        print(f"dalaran-sdk built in {elapsed:.1f} seconds")
        print()

    examples = [
        # Trivial examples that don't require weird dependencies, or downloading data
        "minimal_options",
        "multithreading",
        "plots",
    ]

    if not parser.parse_args().no_install:
        print("----------------------------------------------------------")
        print("Installing examples…")
        start_time = time.time()
        # It's important we use --inexact and --no-install-package here to avoid
        # reinstalling dalaran-sdk and potentially messing up the. Environment
        # This script is sometimes used in CI where dalaran-sdk is already installed
        # from wheel, using the `--no-build` option above.
        args = ["uv", "sync", "--inexact", "--no-install-package", "dalaran-sdk"]
        for example in examples:
            # install in editable mode so `__file__` relative paths work
            args.extend(["--package", example])
        subprocess.run(args, check=True)
        elapsed = time.time() - start_time
        print(f"uv sync in {elapsed:.1f} seconds")
        print()

    for example in examples:
        print("----------------------------------------------------------")
        print(f"Testing {example}…\n")
        start_time = time.time()
        run_example(Path(example).name, [])
        elapsed = time.time() - start_time
        print(f"{example} done in {elapsed:.1f} seconds")
        print()

    print()
    print("All tests passed successfully!")


def run_example(example: str, extra_args: list[str]) -> None:
    env = os.environ.copy()

    # raise exception on warnings, e.g. when using a @deprecated function:
    env["PYTHONWARNINGS"] = "error"

    env["DALARAN_STRICT"] = "1"
    env["DALARAN_PANIC_ON_WARN"] = "1"

    cmd = ["uvpy", "-m", "dalaran", "--port", str(PORT), "--test-receive"]
    dalaran_process = subprocess.Popen(cmd, env=env)
    time.sleep(0.5)  # Wait for dalaran server to start to remove a logged warning

    cmd = ["uvpy", "-m", example, "--connect", "--url", f"dalaran+http://127.0.0.1:{PORT}/proxy", *extra_args]
    python_process = subprocess.Popen(cmd, env=env)

    print("Waiting for python process to finish…")
    returncode = python_process.wait(timeout=30)
    assert returncode == 0, f"python process exited with error code {returncode}"

    print("Waiting for dalaran process to finish…")
    returncode = dalaran_process.wait(timeout=30)
    assert returncode == 0, f"dalaran process exited with error code {returncode}"


if __name__ == "__main__":
    main()
