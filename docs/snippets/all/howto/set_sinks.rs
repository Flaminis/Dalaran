//! Connect to the viewer and log some data.

use dalaran::{demo_util::grid, external::glam};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_attach_sinks")
        .set_sinks((
            // Connect to an existing local Viewer or gRPC server.
            dalaran::sink::GrpcSink::default(),
            // To host a gRPC server instead, replace the sink above with:
            // dalaran::grpc_server::GrpcServerSink::new(
            //     "0.0.0.0",
            //     dalaran::DEFAULT_SERVER_PORT,
            //     dalaran::ServerOptions::default(),
            // )?,
            // Write data to a `data.dlr` file in the current directory.
            dalaran::sink::FileSink::new("data.dlr")?,
        ))?;

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
