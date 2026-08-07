use dl_chunk_store::RowId;
use dl_log_types::TimePoint;
use dl_test_context::TestContext;
use dl_test_viewport::TestContextExt as _;
use dl_viewer_context::{ViewClass as _, ViewId};
use dl_viewport_blueprint::ViewBlueprint;

#[test]
pub fn test_opacity_2d() {
    let mut test_context = TestContext::new_with_view_class::<dl_view_spatial::SpatialView2D>();

    // Tests
    // * the heuristics (the RGB should become transparent)
    // * actual opacity

    {
        use ndarray::{Array, ShapeBuilder as _, s};

        test_context.log_entity("2d_layering/gradient", |builder| {
            let (width, height) = (100, 50);
            let mut image = Array::<u8, _>::zeros((height, width, 3).f());
            image.slice_mut(s![.., .., 0]).fill(0);
            image.slice_mut(s![.., .., 1]).fill(255);
            image.slice_mut(s![.., .., 2]).fill(127);

            builder.with_archetype(
                RowId::new(),
                TimePoint::default(),
                &dl_sdk_types::archetypes::Image::from_color_model_and_tensor(
                    dl_sdk_types::datatypes::ColorModel::RGB,
                    image,
                )
                .unwrap()
                .with_draw_order(1.0),
            )
        });

        test_context.log_entity("2d_layering/depth", |builder| {
            let (width, height) = (50, 100);
            let mut image = Array::<u16, _>::zeros((height, width).f());
            image.slice_mut(s![.., ..]).fill(255);

            let (vec, offset) = image.into_raw_vec_and_offset();
            assert_eq!(offset, Some(0));

            builder.with_archetype(
                RowId::new(),
                TimePoint::default(),
                &dl_sdk_types::archetypes::DepthImage::from_gray16(
                    bytemuck::cast_slice::<u16, u8>(&vec),
                    [width as _, height as _],
                ),
            )
        });
    }

    let view_id = test_context.setup_viewport_blueprint(|_ctx, blueprint| {
        blueprint.add_view_at_root(ViewBlueprint::new_with_root_wildcard(
            dl_view_spatial::SpatialView2D::identifier(),
        ))
    });
    run_view_ui_and_save_snapshot(
        &test_context,
        view_id,
        "opacity_2d",
        egui::vec2(100.0, 100.0) * 2.0,
    );
}

fn run_view_ui_and_save_snapshot(
    test_context: &TestContext,
    view_id: ViewId,
    name: &str,
    size: egui::Vec2,
) {
    let mut harness = test_context
        .setup_kittest_for_rendering_3d(size)
        .build_ui(|ui| {
            test_context.run_with_single_view(ui, view_id);
        });

    harness.run();
    harness.snapshot(name);
}
