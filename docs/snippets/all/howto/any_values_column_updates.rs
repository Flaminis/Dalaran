//! Update custom user-defined values over time, in a single operation.
//!
//! This is semantically equivalent to the `any_values_row_updates` example, albeit much faster.

#![expect(clippy::from_iter_instead_of_collect)]

use std::sync::Arc;

use dalaran::{TimeColumn, external::arrow};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new(
        "dalaran_example_any_values_column_updates",
    )
    .spawn()?;

    const STEPS: i64 = 64;

    let times = TimeColumn::new_sequence("step", 0..STEPS);

    let sin = dalaran::SerializedComponentBatch::new(
        Arc::new(arrow::array::Float64Array::from_iter(
            (0..STEPS).map(|v| ((v as f64) / 10.0).sin()),
        )),
        dalaran::ComponentDescriptor::partial("sin"),
    );

    let cos = dalaran::SerializedComponentBatch::new(
        Arc::new(arrow::array::Float64Array::from_iter(
            (0..STEPS).map(|v| ((v as f64) / 10.0).cos()),
        )),
        dalaran::ComponentDescriptor::partial("cos"),
    );

    rec.send_columns(
        "/",
        [times],
        [
            sin.partitioned(std::iter::repeat_n(1, STEPS as _))?,
            cos.partitioned(std::iter::repeat_n(1, STEPS as _))?,
        ],
    )?;

    Ok(())
}
