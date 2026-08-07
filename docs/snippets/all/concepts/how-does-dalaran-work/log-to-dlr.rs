fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Open a local file handle to stream the data into.
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_log_to_dlr")
        .save("/tmp/my_recording.dlr")?;

    // Log data as usual, thereby writing it into the file.
    loop {
        rec.log("/", &dalaran::TextLog::new("Logging things…"))?;
    }
}
