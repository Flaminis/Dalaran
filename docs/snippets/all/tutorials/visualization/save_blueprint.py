"""Craft an example blueprint with the python API and save it to a file."""

import sys

import dalaran.blueprint as dlb

path_to_rbl = sys.argv[1]

dlb.Blueprint(
    dlb.Horizontal(
        dlb.Grid(
            dlb.BarChartView(name="Bar Chart", origin="/bar_chart"),
            dlb.TimeSeriesView(
                name="Curves",
                origin="/curves",
            ),
        ),
        dlb.TextDocumentView(name="Description", origin="/description"),
        column_shares=[3, 1],
    ),
    dlb.SelectionPanel(state="collapsed"),
    dlb.TimePanel(state="collapsed"),
).save("your_blueprint_name", path_to_rbl)
