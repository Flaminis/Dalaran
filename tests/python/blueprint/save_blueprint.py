from __future__ import annotations

import dalaran.blueprint as dlb

blueprint = dlb.Blueprint(
    dlb.Spatial3DView(origin="/test1"),
    dlb.TimePanel(state="collapsed"),
    dlb.SelectionPanel(state="collapsed"),
    dlb.BlueprintPanel(state="collapsed"),
)

blueprint.save("dalaran_example_blueprint_test.dbl")
