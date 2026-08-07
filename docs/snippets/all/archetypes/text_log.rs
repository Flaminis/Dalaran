//! Log a `TextLog`

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_text_log").spawn()?;

    rec.log(
        "log",
        &dalaran::TextLog::new("Application started.").with_level("INFO"),
    )?;

    Ok(())
}
