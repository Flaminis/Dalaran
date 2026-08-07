//! Log a single 3D box.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_box3d").spawn()?;

    rec.log(
        "simple",
        &dalaran::Boxes3D::from_half_sizes([(2.0, 2.0, 1.0)]),
    )?;

    Ok(())
}
