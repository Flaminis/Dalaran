//! Log a simple line strip.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_line_strip2d")
        .spawn()?;

    let points = [[0., 0.], [2., 1.], [4., -1.], [6., 0.]];
    rec.log("strip", &dalaran::LineStrips2D::new([points]))?;

    // TODO(#5521): log VisualBounds2D

    Ok(())
}
