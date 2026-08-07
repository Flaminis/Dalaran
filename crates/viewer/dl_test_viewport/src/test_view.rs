use dl_chunk::EntityPath;
use dl_log_types::example_components::MyPoint;
use dl_sdk_types::Archetype as _;
use dl_ui::Help;
use dl_viewer_context::external::dl_chunk_store::external::dl_chunk;
use dl_viewer_context::{
    IdentifiedViewSystem, ViewClass, ViewSpawnHeuristics, ViewState, ViewerContext,
    VisualizerExecutionOutput, VisualizerQueryInfo, VisualizerSystem, suggest_view_for_each_entity,
};

#[derive(Default)]
pub struct TestView;

#[derive(dl_byte_size::SizeBytes)]
pub struct TestViewState;

impl ViewState for TestViewState {
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }

    fn as_any_mut(&mut self) -> &mut dyn std::any::Any {
        self
    }

    fn heap_size_bytes(&self) -> u64 {
        dl_viewer_context::SizeBytes::heap_size_bytes(self)
    }
}

#[derive(Default)]
pub struct TestSystem;

impl VisualizerSystem for TestSystem {
    fn visualizer_query_info(
        &self,
        _app_options: &dl_viewer_context::AppOptions,
    ) -> dl_viewer_context::VisualizerQueryInfo {
        VisualizerQueryInfo::single_required_component::<MyPoint>(
            &dl_log_types::example_components::MyPoints::descriptor_points(),
            &dl_log_types::example_components::MyPoints::all_components(),
        )
    }

    fn execute(
        &self,
        _ctx: &dl_viewer_context::ViewContext<'_>,
        _query: &dl_viewer_context::ViewQuery<'_>,
        _context_systems: &dl_viewer_context::ViewContextCollection,
    ) -> Result<VisualizerExecutionOutput, dl_viewer_context::ViewSystemExecutionError> {
        Ok(VisualizerExecutionOutput::default())
    }
}

impl IdentifiedViewSystem for TestSystem {
    fn identifier() -> dl_viewer_context::ViewSystemIdentifier {
        dl_viewer_context::external::dl_string_interner::intern_static!(
            dl_viewer_context::ViewSystemIdentifier,
            "Test"
        )
    }
}

impl ViewClass for TestView {
    fn identifier() -> dl_sdk_types::ViewClassIdentifier
    where
        Self: Sized,
    {
        "TestView".into()
    }

    fn display_name(&self) -> &'static str {
        "Test view"
    }

    fn help(&self, _os: egui::os::OperatingSystem) -> dl_ui::Help {
        Help::new("Test view").markdown("Only used in tests.")
    }

    fn on_register(
        &self,
        system_registry: &mut dl_viewer_context::ViewSystemRegistrator<'_>,
    ) -> Result<(), dl_viewer_context::ViewClassRegistryError> {
        system_registry.register_visualizer::<TestSystem>()?;

        system_registry
            .register_fallback_provider(MyPoint::partial_descriptor().component, |_ctx| {
                MyPoint::new(0.0, 0.0)
            });

        Ok(())
    }

    fn new_state(&self) -> Box<dyn dl_viewer_context::ViewState> {
        Box::new(TestViewState {})
    }

    fn layout_priority(&self) -> dl_viewer_context::ViewClassLayoutPriority {
        dl_viewer_context::ViewClassLayoutPriority::Low
    }

    fn spawn_heuristics(
        &self,
        ctx: &ViewerContext<'_>,
        include_entity: &dyn Fn(&EntityPath) -> bool,
    ) -> ViewSpawnHeuristics {
        suggest_view_for_each_entity::<TestSystem>(ctx, include_entity)
    }

    fn ui(
        &self,
        _ctx: &ViewerContext<'_>,
        _missing_chunk_reporter: &dl_viewer_context::MissingChunkReporter,
        ui: &mut egui::Ui,
        _state: &mut dyn dl_viewer_context::ViewState,
        _query: &dl_viewer_context::ViewQuery<'_>,
        _system_output: dl_viewer_context::SystemExecutionOutput,
    ) -> Result<dl_viewer_context::ViewClassUiOutput, dl_viewer_context::ViewSystemExecutionError>
    {
        ui.label("Test view");
        Ok(Default::default())
    }
}
