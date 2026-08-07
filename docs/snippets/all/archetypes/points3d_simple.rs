//! Log some very simple points.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_points3d").spawn()?;

    rec.log(
        "points",
        &dalaran::Points3D::new([(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]),
    )?;

    Ok(())
}
