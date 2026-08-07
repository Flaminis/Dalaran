//! Log a simple MCAP schema definition.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_mcap_schema")
        .spawn()?;

    // Example ROS2 message definition for a simple Point message
    let point_schema = "float64 x\nfloat64 y\nfloat64 z";

    rec.log(
        "mcap/schemas/geometry_point",
        &dalaran::McapSchema::new(
            42,
            "geometry_msgs/msg/Point",
            "ros2msg",
            point_schema.as_bytes(),
        ),
    )?;

    Ok(())
}
