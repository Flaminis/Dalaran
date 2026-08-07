fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Connect to the Dalaran gRPC server using the default address and
    // port: localhost:9876
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_log_to_grpc")
        .connect_grpc()?;

    // Log data as usual, thereby pushing it into the stream.
    loop {
        rec.log("/", &dalaran::TextLog::new("Logging things…"))?;
    }
}
