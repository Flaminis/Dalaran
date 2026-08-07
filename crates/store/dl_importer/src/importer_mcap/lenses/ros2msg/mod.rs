use dl_lenses::{LensBuilderError, Lenses};

/// Adds all ROS 2 message lenses to an existing collection.
pub fn add_ros2msg_lenses(lenses: Lenses) -> Result<Lenses, LensBuilderError> {
    Ok(dl_lenses::semantic::ros2msg::all()?
        .into_iter()
        .fold(lenses, Lenses::add_lens))
}
