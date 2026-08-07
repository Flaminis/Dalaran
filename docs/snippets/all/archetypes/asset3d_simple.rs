//! Log a simple 3D asset.

use dalaran::external::anyhow;

fn main() -> anyhow::Result<()> {
    let args = std::env::args().collect::<Vec<_>>();
    let Some(path) = args.get(1) else {
        anyhow::bail!("Usage: {} <path_to_asset.[gltf|glb|obj|stl]>", args[0]);
    };

    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_asset3d").spawn()?;

    rec.log_static("world", &dalaran::ViewCoordinates::RIGHT_HAND_Z_UP())?; // Set the 3D view's up direction
    rec.log("world/asset", &dalaran::Asset3D::from_file_path(path)?)?;

    Ok(())
}
