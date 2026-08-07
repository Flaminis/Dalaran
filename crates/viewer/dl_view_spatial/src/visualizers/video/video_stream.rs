use dl_sdk_types::Archetype as _;
use dl_sdk_types::archetypes::VideoStream;
use dl_sdk_types::components::VideoCodec;
use dl_view::DataResultQuery as _;
use dl_viewer_context::{
    IdentifiedViewSystem, VideoStreamProcessingError, ViewClass as _, ViewContext,
    ViewContextCollection, ViewQuery, ViewSystemExecutionError, VisualizerExecutionOutput,
    VisualizerQueryInfo, VisualizerSystem,
};

use crate::visualizers::SpatialViewVisualizerData;
use crate::visualizers::video::{VideoStreamCtx, execute_video_stream_like};

#[derive(Default)]
pub struct VideoStreamVisualizer;

impl IdentifiedViewSystem for VideoStreamVisualizer {
    fn identifier() -> dl_viewer_context::ViewSystemIdentifier {
        dl_viewer_context::external::dl_string_interner::intern_static!(
            dl_viewer_context::ViewSystemIdentifier,
            "VideoStream"
        )
    }
}

impl VisualizerSystem for VideoStreamVisualizer {
    fn visualizer_query_info(
        &self,
        _app_options: &dl_viewer_context::AppOptions,
    ) -> VisualizerQueryInfo {
        VisualizerQueryInfo::single_required_component::<VideoCodec>(
            &VideoStream::descriptor_codec(),
            &VideoStream::all_components(),
        )
    }

    fn affinity(&self) -> Option<dl_sdk_types::ViewClassIdentifier> {
        Some(crate::SpatialView2D::identifier())
    }

    fn execute(
        &self,
        ctx: &ViewContext<'_>,
        view_query: &ViewQuery<'_>,
        context_systems: &ViewContextCollection,
    ) -> Result<VisualizerExecutionOutput, ViewSystemExecutionError> {
        dl_tracing::profile_function!();

        let mut data = SpatialViewVisualizerData::default();

        let ctx = VideoStreamCtx::new(
            ctx,
            view_query,
            context_systems,
            &mut data,
            Self::identifier(),
            VideoStream::name(),
            VideoStream::descriptor_sample().component,
            &|ctx, latest_at, data_result, instruction, output| {
                let codec_component = VideoStream::descriptor_codec().component;
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
                    .get_mono::<VideoCodec>(codec_component)
                    .ok_or(VideoStreamProcessingError::MissingCodec)?;
                Ok(codec.into())
            },
        )
        .with_opacity_component(VideoStream::descriptor_opacity().component);

        execute_video_stream_like(ctx)
    }
}
