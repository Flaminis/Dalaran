//! Log some very simple points.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_points2d").spawn()?;

    rec.log("points", &dalaran::Points2D::new([(0.0, 0.0), (1.0, 1.0)]))?;

    // TODO(#5521): log VisualBounds2D

    Ok(())
}
