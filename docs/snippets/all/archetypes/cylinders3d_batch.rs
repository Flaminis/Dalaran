//! Log a batch of cylinders.

use dalaran::external::glam::vec3;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_cylinders3d_batch")
            .spawn()?;

    rec.log(
        "cylinders",
        &dalaran::Cylinders3D::from_lengths_and_radii(
            [0.0, 2.0, 4.0, 6.0, 8.0],
            [1.0, 0.5, 0.5, 0.5, 1.0],
        )
        .with_colors([
            dalaran::Color::from_rgb(255, 0, 0),
            dalaran::Color::from_rgb(188, 188, 0),
            dalaran::Color::from_rgb(0, 255, 0),
            dalaran::Color::from_rgb(0, 188, 188),
            dalaran::Color::from_rgb(0, 0, 255),
        ])
        .with_centers([
            vec3(0., 0., 0.),
            vec3(2., 0., 0.),
            vec3(4., 0., 0.),
            vec3(6., 0., 0.),
            vec3(8., 0., 0.),
        ])
        .with_rotation_axis_angles((0..5).map(|i| {
            dalaran::RotationAxisAngle::new(
                [1.0, 0.0, 0.0],
                dalaran::Angle::from_degrees(i as f32 * -22.5),
            )
        })),
    )?;

    Ok(())
}
