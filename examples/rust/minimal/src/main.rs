//! Demonstrates the most barebone usage of the Dalaran SDK.

use dalaran::demo_util::grid;
use dalaran::external::glam;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_minimal").spawn()?;

    let points = grid(glam::Vec3::splat(-10.0), glam::Vec3::splat(10.0), 10);
    let colors = grid(glam::Vec3::ZERO, glam::Vec3::splat(255.0), 10)
        .map(|v| dalaran::Color::from_rgb(v.x as u8, v.y as u8, v.z as u8));

    rec.log(
        "my_points",
        &dalaran::Points3D::new(points)
            .with_colors(colors)
            .with_radii([0.5]),
    )?;

    Ok(())
}
