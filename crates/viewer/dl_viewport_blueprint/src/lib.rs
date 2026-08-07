//! Dalaran Viewport Blueprint
//!
//! This crate provides blueprint (i.e. description) for how to render the viewport.

mod auto_layout;
mod container;
mod entity_add_info;
pub mod ui;
mod view;
mod view_contents;
mod view_properties;
mod viewport_blueprint;
mod viewport_command;

#[cfg(test)]
mod test_view_class;

pub use container::ContainerBlueprint;
use dl_chunk::EntityPath;
use dl_viewer_context::ViewerContext;
pub use entity_add_info::{CanAddToView, EntityAddInfo, create_entity_add_info};
pub use view::ViewBlueprint;
pub use view_contents::ViewContents;
pub use view_properties::{ViewProperty, ViewPropertyQueryError, entity_path_for_view_property};
pub use viewport_blueprint::{ViewportBlueprint, tree_simplification_options};
pub use viewport_command::ViewportCommand;

/// The entity path of the viewport blueprint in the blueprint store.
pub const VIEWPORT_PATH: &str = "viewport";

/// Converts a [`dl_sdk_types::blueprint::components::ContainerKind`] into a [`egui_tiles::ContainerKind`].
///
/// Does not implement the `From`/`To` traits because we don't want `dl_sdk_types` to depend
/// on `egui`, and we cannot do it from here because of orphan rules.
#[inline]
pub fn container_kind_to_egui(
    kind: dl_sdk_types::blueprint::components::ContainerKind,
) -> egui_tiles::ContainerKind {
    use dl_sdk_types::blueprint::components::ContainerKind;
    match kind {
        ContainerKind::Tabs => egui_tiles::ContainerKind::Tabs,
        ContainerKind::Horizontal => egui_tiles::ContainerKind::Horizontal,
        ContainerKind::Vertical => egui_tiles::ContainerKind::Vertical,
        ContainerKind::Grid => egui_tiles::ContainerKind::Grid,
    }
}

/// Converts a [`egui_tiles::ContainerKind`] into a [`dl_sdk_types::blueprint::components::ContainerKind`].
///
/// Does not implement the `From`/`To` traits because we don't want `dl_sdk_types` to depend
/// on `egui`, and we cannot do it from here because of orphan rules.
#[inline]
pub fn container_kind_from_egui(
    kind: egui_tiles::ContainerKind,
) -> dl_sdk_types::blueprint::components::ContainerKind {
    use dl_sdk_types::blueprint::components::ContainerKind;
    match kind {
        egui_tiles::ContainerKind::Tabs => ContainerKind::Tabs,
        egui_tiles::ContainerKind::Horizontal => ContainerKind::Horizontal,
        egui_tiles::ContainerKind::Vertical => ContainerKind::Vertical,
        egui_tiles::ContainerKind::Grid => ContainerKind::Grid,
    }
}

/// List out all views we generate by default for the available data.
///
/// TODO(andreas): This is transitional. We want to pass on the view spawn heuristics
/// directly and make more high level decisions with it.
pub fn default_created_views(ctx: &ViewerContext<'_>) -> Vec<ViewBlueprint> {
    dl_tracing::profile_function!();

    ctx.view_class_registry()
        .iter_registry()
        .flat_map(|entry| {
            let include_entity = |_: &EntityPath| true;
            let spawn_heuristics = entry.class.spawn_heuristics(ctx, &include_entity);
            spawn_heuristics
                .into_vec()
                .into_iter()
                .map(|recommendation| ViewBlueprint::new(entry.identifier, recommendation))
        })
        .collect()
}
