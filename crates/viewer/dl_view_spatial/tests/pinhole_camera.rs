use dl_chunk_store::RowId;
use dl_log_types::TimePoint;
use dl_sdk_types::archetypes::Pinhole;
use dl_sdk_types::blueprint::archetypes::EyeControls3D;
use dl_sdk_types::components::{Color, Position3D, Radius};
use dl_test_context::TestContext;
use dl_test_viewport::TestContextExt as _;
use dl_viewer_context::{ViewClass as _, ViewId};
use dl_viewport_blueprint::{ViewBlueprint, ViewProperty};

#[test]
pub fn test_pinhole_camera() {
    let mut test_context = TestContext::new_with_view_class::<dl_view_spatial::SpatialView3D>();

    test_context.log_entity("world/camera", |builder| {
        builder.with_archetype(
            RowId::new(),
            TimePoint::default(),
            &Pinhole::from_focal_length_and_resolution([3., 3.], [3., 3.])
                .with_color(Color::from_rgb(255, 144, 1)) // #FF9001
                .with_line_width(Radius::new_ui_points(2.0)),
        )
    });

    let view_id = test_context.setup_viewport_blueprint(|_ctx, blueprint| {
        let view =
            ViewBlueprint::new_with_root_wildcard(dl_view_spatial::SpatialView3D::identifier());
        blueprint.add_view_at_root(view)
    });

    run_view_ui_and_save_snapshot(&test_context, view_id, egui::vec2(300.0, 300.0));
}

fn run_view_ui_and_save_snapshot(test_context: &TestContext, view_id: ViewId, size: egui::Vec2) {
    let mut harness = test_context
        .setup_kittest_for_rendering_3d(size)
        .build_ui(|ui| {
            test_context.run_with_single_view(ui, view_id);
        });

    test_context.with_blueprint_ctx(|ctx, _| {
        ViewProperty::from_archetype_for_view::<EyeControls3D>(&ctx, view_id)
            .save_blueprint_component(
                &ctx,
                &EyeControls3D::descriptor_position(),
                &Position3D::new(1.0, 1.0, 1.0),
            );
    });
    harness.run_steps(10);

    harness.snapshot("pinhole_camera");
}
