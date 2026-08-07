//! Log different transforms with visualized coordinates axes.

use dalaran::AsComponents;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_transform3d_axes")
            .spawn()?;

    rec.set_time_sequence("step", 0);

    rec.log(
        "base",
        &[
            &dalaran::Transform3D::new() as &dyn AsComponents,
            &dalaran::TransformAxes3D::new(1.0),
        ],
    )?;

    for deg in 0..360 {
        rec.set_time_sequence("step", deg);
        rec.log(
            "base/rotated",
            &[
                &dalaran::Transform3D::new().with_rotation(
                    dalaran::RotationAxisAngle::new(
                        [1.0, 1.0, 1.0],
                        dalaran::Angle::from_degrees(deg as f32),
                    ),
                ) as &dyn AsComponents,
                &dalaran::TransformAxes3D::new(0.5),
            ],
        )?;
        rec.log(
            "base/rotated/translated",
            &[
                &dalaran::Transform3D::new().with_translation([2.0, 0.0, 0.0])
                    as &dyn AsComponents,
                &dalaran::TransformAxes3D::new(0.5),
            ],
        )?;
    }

    Ok(())
}
