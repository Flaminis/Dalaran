//! Log a simple 3D box with a regular & instance pose transform.

use dalaran::{
    demo_util::grid,
    external::{anyhow, glam},
};

fn main() -> anyhow::Result<()> {
    let rec = dalaran::RecordingStreamBuilder::new(
        "dalaran_example_instance_pose3d_combined",
    )
    .spawn()?;

    rec.set_time_sequence("frame", 0);

    // Log a box and points further down in the hierarchy.
    rec.log(
        "world/box",
        &dalaran::Boxes3D::from_half_sizes([[1.0, 1.0, 1.0]]),
    )?;
    rec.log(
        "world/box/points",
        &dalaran::Points3D::new(grid(
            glam::Vec3::splat(-10.0),
            glam::Vec3::splat(10.0),
            10,
        )),
    )?;

    for i in 0..180 {
        rec.set_time_sequence("frame", i);

        // Log a regular transform which affects both the box and the points.
        rec.log(
            "world/box",
            &dalaran::Transform3D::from_rotation(dalaran::RotationAxisAngle {
                axis: [0.0, 0.0, 1.0].into(),
                angle: dalaran::Angle::from_degrees(i as f32 * 2.0),
            }),
        )?;

        // Log an instance pose which affects only the box.
        let translation = [0.0, 0.0, (i as f32 * 0.1 - 5.0).abs() - 5.0];
        rec.log(
            "world/box",
            &dalaran::InstancePoses3D::new().with_translations([translation]),
        )?;
    }

    Ok(())
}
