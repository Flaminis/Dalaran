"""Craft a blueprint with the python API and save it to file."""

import sys

import dalaran.blueprint as dlb

path_to_rbl = sys.argv[1]

blueprint = dlb.Blueprint(
    dlb.TimeSeriesView(name="AAPL", origin="/stocks/AAPL"),
)

# Save to a file
blueprint.save("dalaran_example_blueprint_stocks", path_to_rbl)
