//! Log arbitrary data.

use std::sync::Arc;

use dalaran::external::arrow;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_any_values")
        .spawn()?;

    let any_values = dalaran::AnyValues::default()
        // Using arbitrary Arrow data.
        .with_component_from_data(
            "homepage",
            Arc::new(arrow::array::StringArray::from(vec![
                "https://www.dalaran.dev",
            ])),
        )
        .with_component_from_data(
            "repository",
            Arc::new(arrow::array::StringArray::from(vec![
                "https://github.com/rerun-io/rerun",
            ])),
        )
        // Using Dalaran's builtin components.
        .with_component::<dalaran::components::Scalar>(
            "confidence",
            [1.2, 3.4, 5.6],
        )
        .with_component::<dalaran::components::Text>(
            "description",
            vec!["Bla bla bla…"],
        );

    rec.log("any_values", &any_values)?;

    Ok(())
}
