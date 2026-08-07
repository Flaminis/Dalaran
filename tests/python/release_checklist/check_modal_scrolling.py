from __future__ import annotations

import os
from argparse import Namespace
from uuid import uuid4

import dalaran as dl
import dalaran.blueprint as dlb

README = """\
# Modal scrolling

* Select the 2D view
* Open the Entity Path Filter modal
* Make sure it behaves properly, including scrolling
"""


def log_readme() -> None:
    dl.log("readme", dl.TextDocument(README, media_type=dl.MediaType.MARKDOWN), static=True)


def log_many_entities() -> None:
    for i in range(1000):
        dl.log(f"points/{i}", dl.Points2D([(i, i)]))


def run(args: Namespace) -> None:
    dl.script_setup(
        args,
        f"{os.path.basename(__file__)}",
        recording_id=uuid4(),
    )
    dl.send_blueprint(
        dlb.Grid(dlb.Spatial2DView(origin="/"), dlb.TextDocumentView(origin="readme")),
        make_active=True,
        make_default=True,
    )

    log_readme()
    log_many_entities()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive release checklist")
    dl.script_add_args(parser)
    args = parser.parse_args()
    run(args)
