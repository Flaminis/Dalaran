mod depth_offsets;
mod transform_tree_context;

pub use depth_offsets::EntityDepthOffsets;
// -----------------------------------------------------------------------------
use dl_renderer::DepthOffset;
use dl_sdk_types::ViewClassIdentifier;
use dl_sdk_types::blueprint::components::VisualizerInstructionId;
use dl_viewer_context::{Annotations, ViewClassRegistryError};
pub use transform_tree_context::{TransformInfo, TransformTreeContext};

/// Context objects for a single visualizer instruction in a spatial scene.
pub struct SpatialSceneVisualizerInstructionContext<'a> {
    pub visualizer_instruction: VisualizerInstructionId,
    pub transform_info: &'a TransformInfo,
    pub depth_offset: DepthOffset,
    pub annotations: std::sync::Arc<Annotations>,

    pub highlight: &'a dl_viewer_context::ViewOutlineMasks, // Not part of the context, but convenient to have here.
    pub view_class_identifier: ViewClassIdentifier,
}

pub fn register_spatial_contexts(
    system_registry: &mut dl_viewer_context::ViewSystemRegistrator<'_>,
) -> Result<(), ViewClassRegistryError> {
    system_registry.register_context_system::<TransformTreeContext>()?;
    system_registry.register_context_system::<EntityDepthOffsets>()?;

    dl_viewer_context::AnnotationContextStoreSubscriber::subscription_handle();

    Ok(())
}
