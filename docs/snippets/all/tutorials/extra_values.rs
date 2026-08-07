//! Log extra values with a `Points2D`.

use std::sync::Arc;

use dalaran::external::arrow;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_extra_values")
        .spawn()?;

    let points = dalaran::Points2D::new([
        (-1.0, -1.0),
        (-1.0, 1.0),
        (1.0, -1.0),
        (1.0, 1.0),
    ]);
    let confidences = dalaran::AnyValues::default().with_component_from_data(
        "confidence",
        Arc::new(arrow::array::Float64Array::from(vec![0.3, 0.4, 0.5, 0.6])),
    );

    rec.log(
        "extra_values",
        &[&points as &dyn dalaran::AsComponents, &confidences],
    )?;

    Ok(())
}
