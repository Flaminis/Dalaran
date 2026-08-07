use dl_log_types::Timestamp;
use dl_sdk_types::datatypes;
use dl_ui::UiLayout;
use dl_ui::syntax_highlighting::SyntaxHighlightedBuilder;
use dl_viewer_context::MaybeMutRef;

pub fn view_timestamp(
    ctx: &dl_viewer_context::AppContext<'_>,
    ui: &mut egui::Ui,
    value: &mut MaybeMutRef<'_, impl std::ops::DerefMut<Target = datatypes::TimeInt>>,
) -> egui::Response {
    let value: &datatypes::TimeInt = value;
    UiLayout::List.data_label(
        ui,
        SyntaxHighlightedBuilder::new()
            .with_primitive(&Timestamp::from(*value).format(ctx.app_options.timestamp_format)),
    )
}
