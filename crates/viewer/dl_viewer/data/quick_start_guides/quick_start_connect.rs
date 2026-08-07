//! Connect to the viewer and log some data.

use dalaran::{demo_util::grid, external::glam};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create a new `RecordingStream` which sends data over gRPC to the viewer process.
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_quick_start_connect").connect_grpc()?;

    // Create some data using the `grid` utility function.
    let points = grid(glam::Vec3::splat(-10.0), glam::Vec3::splat(10.0), 10);
    let colors = grid(glam::Vec3::ZERO, glam::Vec3::splat(255.0), 10)
        .map(|v| dalaran::Color::from_rgb(v.x as u8, v.y as u8, v.z as u8));

    // Log the "my_points" entity with our data, using the `Points3D` archetype.
    rec.log(
        "my_points",
        &dalaran::Points3D::new(points)
            .with_colors(colors)
            .with_radii([0.5]),
    )?;

    Ok(())
}
