//! Log a simple line strip.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_line_strip3d")
        .spawn()?;

    let points = [
        [0., 0., 0.],
        [0., 0., 1.],
        [1., 0., 0.],
        [1., 0., 1.],
        [1., 1., 0.],
        [1., 1., 1.],
        [0., 1., 0.],
        [0., 1., 1.],
    ];
    rec.log("strip", &dalaran::LineStrips3D::new([points]))?;

    Ok(())
}
