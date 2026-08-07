//! Create and set a file sink.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_file_sink")
        .buffered()?;

    rec.set_sink(Box::new(dalaran::sink::FileSink::new("recording.dlr")?));

    Ok(())
}
