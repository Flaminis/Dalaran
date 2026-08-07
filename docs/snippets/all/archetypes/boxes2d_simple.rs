//! Log some very simple 2D boxes.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_box2d").spawn()?;

    rec.log(
        "simple",
        &dalaran::Boxes2D::from_mins_and_sizes([(-1., -1.)], [(2., 2.)]),
    )?;

    Ok(())
}
