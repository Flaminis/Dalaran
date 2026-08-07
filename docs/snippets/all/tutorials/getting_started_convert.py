from dalaran.experimental import McapReader

McapReader("input.mcap").stream().write_dlr(
    "run-1.dlr",
    application_id="dalaran_example_getting_started",
    recording_id="run-1",
)
