use dl_sdk_types::Archetype as _;
use dl_sdk_types::archetypes::EncodedImage;
use dl_sdk_types::components::{Blob, MediaType};
use dl_view::DataResultQuery as _;
use dl_viewer_context::{
    IdentifiedViewSystem, ViewClass as _, ViewContext, ViewContextCollection, ViewQuery,
    ViewSystemExecutionError, VisualizerExecutionOutput, VisualizerQueryInfo, VisualizerSystem,
};

use super::SpatialViewVisualizerData;
use crate::visualizers::video::{VideoStreamCtx, execute_video_stream_like};

#[derive(Default)]
pub struct EncodedImageVisualizer;

impl IdentifiedViewSystem for EncodedImageVisualizer {
    fn identifier() -> dl_viewer_context::ViewSystemIdentifier {
        dl_viewer_context::external::dl_string_interner::intern_static!(
            dl_viewer_context::ViewSystemIdentifier,
            "EncodedImage"
        )
    }
}

impl VisualizerSystem for EncodedImageVisualizer {
    fn affinity(&self) -> Option<dl_sdk_types::ViewClassIdentifier> {
        Some(crate::SpatialView2D::identifier())
    }

    fn visualizer_query_info(
        &self,
        _app_options: &dl_viewer_context::AppOptions,
    ) -> VisualizerQueryInfo {
        VisualizerQueryInfo::single_required_component::<Blob>(
            &EncodedImage::descriptor_blob(),
            &EncodedImage::all_components(),
        )
    }

    fn execute(
        &self,
        ctx: &ViewContext<'_>,
        view_query: &ViewQuery<'_>,
        context_systems: &ViewContextCollection,
    ) -> Result<VisualizerExecutionOutput, ViewSystemExecutionError> {
        dl_tracing::profile_function!();

        let mut data = SpatialViewVisualizerData::default();

        let get_codec: &crate::visualizers::video::GetCodecFn =
            &|ctx, latest_at, data_result, instruction, output| {
                let codec_component = EncodedImage::descriptor_media_type().component;
                let results = data_result.latest_at_with_blueprint_resolved_data_for_component(
                    ctx,
                    latest_at,
                    codec_component,
                    Some(instruction),
                );
                if results.any_missing_chunks() {
                    output.set_missing_chunks();
                }

                let codec = results
                    .get_mono::<MediaType>(codec_component)
                    .map(|m| m.to_string());
                Ok(dl_video::VideoCodec::ImageSequence(codec))
            };

        let ctx = VideoStreamCtx::new(
            ctx,
            view_query,
            context_systems,
            &mut data,
            Self::identifier(),
            EncodedImage::name(),
            EncodedImage::descriptor_blob().component,
            &get_codec,
        )
        .with_opacity_component(EncodedImage::descriptor_opacity().component);

        execute_video_stream_like(ctx)
    }
}
