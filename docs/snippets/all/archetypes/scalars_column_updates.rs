//! Update a scalar over time, in a single operation.
//!
//! This is semantically equivalent to the `scalar_row_updates` example, albeit much faster.

use dalaran::TimeColumn;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new(
        "dalaran_example_scalar_column_updates",
    )
    .spawn()?;

    let times = TimeColumn::new_sequence("step", 0..64);
    let scalars = (0..64).map(|step| (step as f64 / 10.0).sin());

    rec.send_columns(
        "scalars",
        [times],
        dalaran::Scalars::new(scalars).columns_of_unit_batches()?,
    )?;

    Ok(())
}
