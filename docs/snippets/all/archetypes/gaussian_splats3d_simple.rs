//! Log a few gaussian splats.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_gaussian_splats3d")
            .spawn()?;

    rec.log(
        "gaussians",
        &dalaran::GaussianSplats3D::new([
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
        ])
        .with_scales([(1.0, 0.5, 0.25), (0.5, 1.0, 0.5), (0.25, 0.5, 1.0)])
        .with_quaternions([
            dalaran::Quaternion::IDENTITY,
            dalaran::Quaternion::from_xyzw([0.0, 0.0, 0.382683, 0.923880]), // 45 degrees around Z
            dalaran::Quaternion::IDENTITY,
        ])
        .with_colors([
            dalaran::Color::from_unmultiplied_rgba(255, 0, 0, 128),
            dalaran::Color::from_unmultiplied_rgba(0, 255, 0, 200),
            dalaran::Color::from_unmultiplied_rgba(0, 0, 255, 255),
        ])
        // 15 view-dependent RGB coefficients (degrees 1-3) per splat, coefficient-major:
        .with_sh_coefficients([
            [[0.5, 0.0, 0.0]; 15],
            [[0.0, 0.5, 0.0]; 15],
            [[0.0, 0.0, 0.5]; 15],
        ]),
    )?;

    Ok(())
}
