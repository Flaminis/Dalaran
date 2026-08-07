//! Log a simple MCAP channel definition.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_mcap_channel")
        .spawn()?;

    rec.log(
        "mcap/channels/camera",
        &dalaran::McapChannel::new(1, "/camera/image", "cdr")
            .with_metadata([("frame_id", "camera_link"), ("encoding", "bgr8")]),
    )?;

    Ok(())
}
