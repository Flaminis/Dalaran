"""Use a blueprint to customize a DataframeView."""

import math

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_dataframe", spawn=True)

# Log some data.
for t in range(int(math.pi * 4 * 100.0)):
    dl.set_time("t", duration=t)
    dl.log("trig/sin", dl.Scalars(math.sin(float(t) / 100.0)))
    dl.log("trig/cos", dl.Scalars(math.cos(float(t) / 100.0)))

    # some sparse data
    if t % 5 == 0:
        dl.log("trig/tan_sparse", dl.Scalars(math.tan(float(t) / 100.0)))

# Create a Dataframe View
blueprint = dlb.Blueprint(
    dlb.DataframeView(
        origin="/trig",
        query=dlb.archetypes.DataframeQuery(
            timeline="t",
            filter_by_range=(dl.TimeInt(seconds=0), dl.TimeInt(seconds=20)),
            filter_is_not_null="/trig/tan_sparse:Scalar",
            select=[
                "t",
                "log_tick",
                "/trig/sin:Scalar",
                "/trig/cos:Scalar",
                "/trig/tan_sparse:Scalar",
            ],
            entity_order=["/trig/cos", "/trig/sin", "/trig/tan_sparse"],
            auto_scroll=True,
        ),
    ),
)

dl.send_blueprint(blueprint)
