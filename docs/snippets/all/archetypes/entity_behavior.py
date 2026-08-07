"""Configure interactivity & visibility of entities."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_entity_behavior", spawn=True)

# Use `EntityBehavior` to override visibility & interactivity of entities
# in the blueprint.
dl.send_blueprint(
    dlb.Spatial2DView(
        overrides={
            "hidden_subtree": dlb.EntityBehavior(visible=False),
            "hidden_subtree/not_hidden": dlb.EntityBehavior(visible=True),
            "non_interactive_subtree": dlb.EntityBehavior(interactive=False),
        }
    )
)

dl.log("hidden_subtree", dl.Points2D(positions=(0, 0), radii=0.5))
dl.log("hidden_subtree/also_hidden", dl.LineStrips2D(strips=[(-1, 1), (1, -1)]))
dl.log("hidden_subtree/not_hidden", dl.LineStrips2D(strips=[(1, 1), (-1, -1)]))
dl.log("non_interactive_subtree", dl.Boxes2D(centers=(0, 0), half_sizes=(1, 1)))
dl.log(
    "non_interactive_subtree/also_non_interactive",
    dl.Boxes2D(centers=(0, 0), half_sizes=(0.5, 0.5)),
)
