use dl_entity_db::InstancePath;
use dl_viewer_context::{StoreViewContext, UiLayout};

use super::DataUi;

impl DataUi for dl_entity_db::EntityPath {
    fn data_ui(&self, ctx: &StoreViewContext<'_>, ui: &mut egui::Ui, ui_layout: UiLayout) {
        InstancePath::entity_all(self.clone()).data_ui(ctx, ui, ui_layout);
    }
}
