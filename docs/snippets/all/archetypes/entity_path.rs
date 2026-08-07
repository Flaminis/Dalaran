//! Example of different ways of constructing an entity path.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_entity_path")
        .spawn()?;

    rec.log(
        r"world/42/escaped\ string\!",
        &dalaran::TextDocument::new("This entity path was escaped manually"),
    )?;
    rec.log(
        dalaran::entity_path!["world", 42, "unescaped string!"],
        &dalaran::TextDocument::new(
            "This entity path was provided as a list of unescaped strings",
        ),
    )?;

    Ok(())
}
