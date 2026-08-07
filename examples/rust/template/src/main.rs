//! Example template.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_my_example_name").spawn()?;

    // … example code
    _ = rec;

    Ok(())
}
