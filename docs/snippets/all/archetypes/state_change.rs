//! Log a `StateChange`

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_state_change")
        .spawn()?;

    rec.set_time_sequence("step", 0);
    rec.log("door", &dalaran::StateChange::single("open"))?;

    rec.set_time_sequence("step", 1);
    rec.log("door", &dalaran::StateChange::single("closed"))?;

    rec.set_time_sequence("step", 2);
    rec.log("door", &dalaran::StateChange::single("open"))?;

    Ok(())
}
