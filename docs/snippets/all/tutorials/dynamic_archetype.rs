//! Log arbitrary archetype data.

use std::sync::Arc;

use dalaran::external::arrow;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_dynamic_archetype")
            .spawn()?;

    let new_archetype = dalaran::DynamicArchetype::new("MyArchetype")
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
                "https://github.com/Flaminis/Dalaran",
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

    rec.log("new_archetype", &new_archetype)?;

    Ok(())
}
