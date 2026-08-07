//! Log a simple 3D mesh with several instance pose transforms which instantiate the mesh several times and will not affect its children (known as mesh instancing).

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_mesh3d_instancing")
            .spawn()?;

    rec.set_time_sequence("frame", 0);
    rec.log(
        "shape",
        &dalaran::Mesh3D::new([
            [1.0, 1.0, 1.0],
            [-1.0, -1.0, 1.0],
            [-1.0, 1.0, -1.0],
            [1.0, -1.0, -1.0],
        ])
        .with_triangle_indices([[0, 2, 1], [0, 3, 1], [0, 3, 2], [1, 3, 2]])
        .with_vertex_colors([
            0xFF0000FF,
            0x00FF00FF,
            0x00000FFFF,
            0xFFFF00FF,
        ]),
    )?;
    // This box will not be affected by its parent's instance poses!
    rec.log(
        "shape/box",
        &dalaran::Boxes3D::from_half_sizes([[5.0, 5.0, 5.0]]),
    )?;

    for i in 0..100 {
        rec.set_time_sequence("frame", i);
        rec.log(
            "shape",
            &dalaran::InstancePoses3D::new()
                .with_translations([
                    [2.0, 0.0, 0.0],
                    [0.0, 2.0, 0.0],
                    [0.0, -2.0, 0.0],
                    [-2.0, 0.0, 0.0],
                ])
                .with_rotation_axis_angles([dalaran::RotationAxisAngle::new(
                    [0.0, 0.0, 1.0],
                    dalaran::Angle::from_degrees(i as f32 * 2.0),
                )]),
        )?;
    }

    Ok(())
}
