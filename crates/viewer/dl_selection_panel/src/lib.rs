//! The UI for the selection panel.

mod defaults_ui;
mod item_heading_no_breadcrumbs;
mod item_heading_with_breadcrumbs;
mod item_title;
mod selection_panel;
mod view_entity_picker;
mod view_space_origin_ui;
mod visible_time_range_ui;
mod visualizer_ui;

pub use selection_panel::SelectionPanel;
pub use visualizer_ui::SourceSelectorContext;

#[cfg(test)]
mod test {
    use dl_chunk_store::LatestAtQuery;
    use dl_viewer_context::{Item, ViewId, blueprint_timeline};
    use dl_viewport_blueprint::ViewportBlueprint;

    use super::*;

    /// This test mainly serve to demonstrate that non-trivial UI code can be executed with a "fake"
    /// [`ViewerContext`].
    // TODO(#6450): check that no warning/error is logged
    #[test]
    fn test_selection_panel() {
        dl_log::setup_logging();

        let test_ctx = dl_test_context::TestContext::new();
        test_ctx.edit_selection(|selection_state| {
            selection_state.set_selection(Item::View(ViewId::random()));
        });

        test_ctx.run_in_egui_central_panel(|ctx, ui| {
            let blueprint = ViewportBlueprint::from_db(
                ctx.store_context.blueprint,
                &LatestAtQuery::latest(blueprint_timeline()),
            );

            let mut selection_panel = SelectionPanel::default();
            selection_panel.show_panel(ctx, &blueprint, &mut Default::default(), ui, &mut true);
        });
    }
}
