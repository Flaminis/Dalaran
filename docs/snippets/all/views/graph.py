"""Use a blueprint to customize a graph view."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_graph_view", spawn=True)

dl.log(
    "simple",
    dl.GraphNodes(
        node_ids=["a", "b", "c"],
        positions=[(0.0, 100.0), (-100.0, 0.0), (100.0, 0.0)],
        labels=["A", "B", "C"],
    ),
)

# Create a Spatial2D view to display the points.
blueprint = dlb.Blueprint(
    dlb.GraphView(
        origin="/",
        name="Graph",
        # Note that this translates the viewbox.
        visual_bounds=dlb.VisualBounds2D(
            x_range=[-150, 150], y_range=[-50, 150]
        ),
        background=dlb.archetypes.GraphBackground(color=[30, 10, 10]),
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
