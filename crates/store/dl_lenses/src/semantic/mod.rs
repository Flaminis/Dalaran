//! Lens definitions for converting third-party semantic schemas to Dalaran components and archetypes.

pub mod foxglove;
pub mod ros2msg;

/// Suffix appended to frame IDs for image planes.
///
/// This matches the Dalaran model for named pinhole frames, where the image plane has its own frame ID.
const IMAGE_PLANE_SUFFIX: &str = "_image_plane";

mod helpers;
mod image_helpers;
