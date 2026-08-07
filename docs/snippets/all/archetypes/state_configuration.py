# Log a `StateChange` together with a `StateConfiguration` that customizes
# its display.

import dalaran as dl

dl.init("dalaran_example_state_configuration", spawn=True)

# Configure how each raw state value is displayed (label, color, visibility).
dl.log(
    "door",
    dl.StateConfiguration(
        values=["open", "closed"],
        labels=["Open", "Closed"],
        colors=[0x4CAF50FF, 0xEF5350FF],
    ),
    static=True,
)

dl.set_time("step", sequence=0)
dl.log("door", dl.StateChange(state="open"))

dl.set_time("step", sequence=1)
dl.log("door", dl.StateChange(state="closed"))

dl.set_time("step", sequence=2)
dl.log("door", dl.StateChange(state="open"))
