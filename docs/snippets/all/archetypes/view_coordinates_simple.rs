//! Set the default orientation for a 3D view.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_view_coordinates")
            .spawn()?;

    rec.log_static("world", &dalaran::ViewCoordinates::RIGHT_HAND_Z_UP())?; // Set the 3D view's up direction
    rec.log(
        "world/xyz",
        &dalaran::Arrows3D::from_vectors(
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], //
        )
        .with_colors([[255, 0, 0], [0, 255, 0], [0, 0, 255]]),
    )?;

    Ok(())
}
