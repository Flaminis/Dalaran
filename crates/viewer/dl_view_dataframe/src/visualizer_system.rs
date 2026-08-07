use dl_viewer_context::{
    IdentifiedViewSystem, ViewContext, ViewContextCollection, ViewQuery, ViewSystemExecutionError,
    VisualizerExecutionOutput, VisualizerQueryInfo, VisualizerSystem,
};

/// An empty system to accept all entities in the view
#[derive(Default)]
pub struct EmptySystem {}

impl IdentifiedViewSystem for EmptySystem {
    fn identifier() -> dl_viewer_context::ViewSystemIdentifier {
        dl_viewer_context::external::dl_string_interner::intern_static!(
            dl_viewer_context::ViewSystemIdentifier,
            "Empty"
        )
    }
}

impl VisualizerSystem for EmptySystem {
    fn visualizer_query_info(
        &self,
        _app_options: &dl_viewer_context::AppOptions,
    ) -> VisualizerQueryInfo {
        VisualizerQueryInfo::empty()
    }

    fn execute(
        &self,
        _ctx: &ViewContext<'_>,
        _query: &ViewQuery<'_>,
        _context_systems: &ViewContextCollection,
    ) -> Result<VisualizerExecutionOutput, ViewSystemExecutionError> {
        Ok(VisualizerExecutionOutput::default())
    }
}
