#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import importlib
from os.path import basename, dirname, isfile, join

import dalaran as dl


def log_checks(args: argparse.Namespace) -> None:
    modules = glob.glob(join(dirname(__file__), "*.py"))
    modules = [basename(f)[:-3] for f in modules if isfile(f) and basename(f).startswith("check_")]

    for module in modules:
        m = importlib.import_module(module)
        m.run(args)


def log_readme() -> None:
    with open(join(dirname(__file__), "README.md"), encoding="utf8") as f:
        dl.log("readme", dl.TextDocument(f.read(), media_type=dl.MediaType.MARKDOWN), static=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive release checklist")
    dl.script_add_args(parser)
    args = parser.parse_args()

    log_checks(args)

    # Log instructions last so that's what people see first.
    dl.script_setup(args, "instructions")
    log_readme()


if __name__ == "__main__":
    main()
