# Log a `StateChange`.

import dalaran as dl

dl.init("dalaran_example_state_change", spawn=True)

dl.set_time("step", sequence=0)
dl.log("door", dl.StateChange(state="open"))

dl.set_time("step", sequence=1)
dl.log("door", dl.StateChange(state="closed"))

dl.set_time("step", sequence=2)
dl.log("door", dl.StateChange(state="open"))
