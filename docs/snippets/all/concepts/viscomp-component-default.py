"""Add a component default."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_component_override", spawn=True)

# Data logged to the data store.
dl.log("boxes/1", dl.Boxes2D(centers=[0, 0], sizes=[1, 1], colors=[255, 0, 0]))
dl.log("boxes/2", dl.Boxes2D(centers=[2, 0], sizes=[1, 1]))

dl.send_blueprint(
    dlb.Spatial2DView(
        overrides={"boxes/1": dl.Boxes2D(colors=[0, 255, 0])},
        # Add a default value for all Color components in this view
        defaults=[dl.Boxes2D.from_fields(colors=[0, 0, 255])],
    ),
)
