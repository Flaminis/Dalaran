"""Override a component."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_component_override", spawn=True)

# Data logged to the data store.
dl.log("boxes/1", dl.Boxes2D(centers=[0, 0], sizes=[1, 1], colors=[255, 0, 0]))
dl.log("boxes/2", dl.Boxes2D(centers=[2, 0], sizes=[1, 1], colors=[255, 0, 0]))

dl.send_blueprint(
    dlb.Spatial2DView(
        # Override the values from the data store for the first box.
        overrides={
            "boxes/1": dl.Boxes2D(colors=[0, 255, 0]),
        },
    ),
)
