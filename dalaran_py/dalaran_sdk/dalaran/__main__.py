"""
See `python3 -m dalaran --help`.

This is a duplicate of `dalaran_cli/__main__.py` to allow running `python3 -m dalaran` directly.
In general `dalaran -m dalaran_cli` should be preferred, as it carries less overhead related to
importing the module.
"""

from __future__ import annotations

import sys

from dalaran_cli.__main__ import main as cli_main

from dalaran import unregister_shutdown


def main() -> int:
    # Importing of the dalaran module registers a shutdown hook that we know we don't
    # need when running the CLI directly. We can safely unregister it.
    unregister_shutdown()

    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
