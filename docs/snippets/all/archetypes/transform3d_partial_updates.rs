//! Update specific properties of a transform over time.

use dalaran::AsComponents;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new(
        "dalaran_example_transform3d_partial_updates",
    )
    .spawn()?;

    // Set up a 3D box.
    rec.log(
        "box",
        &[&dalaran::Boxes3D::from_half_sizes([(4.0, 2.0, 1.0)])
            .with_fill_mode(dalaran::FillMode::Solid)
            as &dyn AsComponents],
    )?;

    // Update only the rotation of the box.
    for deg in 0..=45 {
        let rad = truncated_radians((deg * 4) as f32);
        rec.log(
            "box",
            &dalaran::Transform3D::new().with_rotation(
                dalaran::RotationAxisAngle::new(
                    [0.0, 1.0, 0.0],
                    dalaran::Angle::from_radians(rad),
                ),
            ),
        )?;
    }

    // Update only the position of the box.
    for t in 0..=50 {
        rec.log(
            "box",
            &dalaran::Transform3D::new().with_translation([
                0.0,
                0.0,
                t as f32 / 10.0,
            ]),
        )?;
    }

    // Update only the rotation of the box.
    for deg in 0..=45 {
        let rad = truncated_radians(((deg + 45) * 4) as f32);
        rec.log(
            "box",
            &dalaran::Transform3D::new().with_rotation(
                dalaran::RotationAxisAngle::new(
                    [0.0, 1.0, 0.0],
                    dalaran::Angle::from_radians(rad),
                ),
            ),
        )?;
    }

    // Clear all of the box's attributes.
    rec.log("box", &dalaran::Transform3D::clear_fields())?;

    Ok(())
}

fn truncated_radians(deg: f32) -> f32 {
    ((deg.to_radians() * 1000.0) as i32) as f32 / 1000.0
}
