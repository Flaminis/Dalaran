//! Log a `StateChange` together with a `StateConfiguration` that customizes its display.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_state_configuration")
            .spawn()?;

    // Configure how each raw state value is displayed (label, color, visibility).
    rec.log_static(
        "door",
        &dalaran::StateConfiguration::new()
            .with_values(["open", "closed"])
            .with_labels(["Open", "Closed"])
            .with_colors([0x4CAF50FFu32, 0xEF5350FFu32]),
    )?;

    rec.set_time_sequence("step", 0);
    rec.log("door", &dalaran::StateChange::single("open"))?;

    rec.set_time_sequence("step", 1);
    rec.log("door", &dalaran::StateChange::single("closed"))?;

    rec.set_time_sequence("step", 2);
    rec.log("door", &dalaran::StateChange::single("open"))?;

    Ok(())
}
