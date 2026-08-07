//! Spawn a new Dalaran Viewer process ready to listen for gRPC connections.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    dalaran::spawn(&dalaran::SpawnOptions::default())?;
    Ok(())
}
