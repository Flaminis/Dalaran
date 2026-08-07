"""Demonstrates the experimental state timeline view."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_howto_state_timeline", spawn=True)

# region: state_config
# Customize how each state value is displayed (label, color, visibility).
# Log as static so the configuration applies for the entire recording.
dl.log(
    "door",
    dl.StateConfiguration(
        values=["open", "closed"],
        labels=["Open", "Closed"],
        colors=[0x4CAF50FF, 0xEF5350FF],
    ),
    static=True,
)
# endregion: state_config

# region: log_changes
# Log state transitions for two entities. Each call marks the start of a new
# state; the previous state implicitly ends. The `/door` lane uses the
# `StateConfiguration` above, while `/window` gets default styling (raw value
# as label, hashed color).
dl.set_time("step", sequence=0)
dl.log("door", dl.StateChange(state="open"))
dl.log("window", dl.StateChange(state="closed"))

dl.set_time("step", sequence=1)
dl.log("door", dl.StateChange(state="closed"))

dl.set_time("step", sequence=3)
dl.log("window", dl.StateChange(state="open"))

dl.set_time("step", sequence=4)
dl.log("door", dl.StateChange(state="open"))
# endregion: log_changes

# region: blueprint
# Place a state timeline view at the root. The viewer will create one
# automatically as soon as it sees `StateChange` data, but the blueprint API
# lets you control the origin, name, and layout explicitly.
blueprint = dlb.Blueprint(
    dlb.StateTimelineView(origin="/", name="Doors and windows"),
)
dl.send_blueprint(blueprint)
# endregion: blueprint
