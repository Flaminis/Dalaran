fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_getting_started")
            .recording_id("run-1")
            .save("run-1.rrd")?;

    for t in 0..10 {
        rec.set_time_sequence("step", t);
        let tf = t as f64;
        rec.log("/arm/shoulder", &dalaran::Scalars::single((tf * 0.5).sin()))?;
        rec.log("/arm/elbow", &dalaran::Scalars::single((tf * 0.5).cos()))?;
    }

    Ok(())
}
