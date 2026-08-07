# Use a blueprint to show a StateTimelineView.

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_state_timeline", spawn=True)

dl.set_time("step", sequence=0)
dl.log("door", dl.StateChange(state="open"))

dl.set_time("step", sequence=1)
dl.log("door", dl.StateChange(state="closed"))

dl.set_time("step", sequence=2)
dl.log("door", dl.StateChange(state="open"))

# Create a state timeline view to display the state transitions.
blueprint = dlb.Blueprint(
    dlb.StateTimelineView(
        origin="/",
        name="State Transitions",
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
