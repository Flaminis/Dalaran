//! Update a scalar over time.
//!
//! See also the `scalar_column_updates` example, which achieves the same thing in a single operation.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_scalar_row_updates")
            .spawn()?;

    for step in 0..64 {
        rec.set_time_sequence("step", step);
        rec.log(
            "scalars",
            &dalaran::Scalars::single((step as f64 / 10.0).sin()),
        )?;
    }

    Ok(())
}
