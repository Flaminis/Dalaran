from __future__ import annotations

import os
from argparse import Namespace
from uuid import uuid4

import dalaran as dl

README = """\
# Plot overrides

This checks whether one can override all properties in a plot.

### Component overrides

* Select `plots/cos`.
* Under "Visualizer": Override all of its properties with arbitrary values.
* Remove all these overrides.

### Visible time range overrides
* Select the `plots` view and confirm it shows:
  * "Default" selected
  * Showing "Entire timeline".
* Select the `plots/cos` entity and confirm it shows:
  * "Default" selected
  * Showing "Entire timeline".
* Override the `plots` view Visible time range
  * Verify all 3 offset modes operate as expected
* Override the `plots/cos` entity Visible time range
  * Verify all 3 offset modes operate as expected

### Overrides are cloned
* After overriding things on both the view and the entity, clone the view.

If nothing weird happens, you can close this recording.
"""


def log_readme() -> None:
    dl.log("readme", dl.TextDocument(README, media_type=dl.MediaType.MARKDOWN), static=True)


def log_plots() -> None:
    from math import cos, sin, tau

    dl.log("plots/sin", dl.SeriesLines(colors=[255, 0, 0], names="sin(0.01t)"), static=True)
    dl.log("plots/cos", dl.SeriesLines(colors=[0, 255, 0], names="cos(0.01t)"), static=True)

    for t in range(int(tau * 2 * 10.0)):
        dl.set_time("frame_nr", sequence=t)

        sin_of_t = sin(float(t) / 10.0)
        dl.log("plots/sin", dl.Scalars(sin_of_t))

        cos_of_t = cos(float(t) / 10.0)
        dl.log("plots/cos", dl.Scalars(cos_of_t))


def run(args: Namespace) -> None:
    dl.script_setup(args, f"{os.path.basename(__file__)}", recording_id=uuid4())

    log_readme()
    log_plots()

    dl.send_blueprint(dl.blueprint.Blueprint(auto_layout=True, auto_views=True), make_active=True, make_default=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive release checklist")
    dl.script_add_args(parser)
    args = parser.parse_args()
    run(args)
