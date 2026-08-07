//! Log a batch of oriented bounding boxes.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_box3d_batch")
        .spawn()?;

    rec.log(
        "batch",
        &dalaran::Boxes3D::from_centers_and_half_sizes(
            [(2.0, 0.0, 0.0), (-2.0, 0.0, 0.0), (0.0, 0.0, 2.0)],
            [(2.0, 2.0, 1.0), (1.0, 1.0, 0.5), (2.0, 0.5, 1.0)],
        )
        .with_quaternions([
            dalaran::Quaternion::IDENTITY,
            dalaran::Quaternion::from_xyzw([0.0, 0.0, 0.382683, 0.923880]), // 45 degrees around Z
        ])
        .with_radii([0.025])
        .with_colors([
            dalaran::Color::from_rgb(255, 0, 0),
            dalaran::Color::from_rgb(0, 255, 0),
            dalaran::Color::from_rgb(0, 0, 255),
        ])
        .with_fill_mode(dalaran::FillMode::Solid)
        .with_labels(["red", "green", "blue"]),
    )?;

    Ok(())
}
