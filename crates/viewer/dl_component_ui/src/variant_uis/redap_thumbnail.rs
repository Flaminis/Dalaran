use std::error::Error;

use dl_sdk_types::components::MediaType;
use dl_types_core::{ComponentIdentifier, Loggable as _, RowId};
use dl_ui::UiLayout;
use dl_viewer_context::AppContext;

/// Display a thumbnail that takes all the available space.
pub fn redap_thumbnail(
    ctx: &AppContext<'_>,
    ui: &mut egui::Ui,
    component: ComponentIdentifier,
    row_id: Option<RowId>,
    data: &dyn arrow::array::Array,
) -> Result<(), Box<dyn Error>> {
    let row_id = row_id.ok_or("RowId is required for redap_thumbnail")?;

    let blobs = dl_sdk_types::components::Blob::from_arrow(data)?;
    let blob = blobs.first().ok_or("Blob data is empty")?;

    let slice = blob.as_ref();

    let media_type = MediaType::guess_from_data(slice);

    // The thumbnail data is catalog data, not tied to any particular store,
    // so this uses the app-level cache.
    #[expect(deprecated)] // TODO(RR-4570): Figure out a way to do this using the video decoder.
    let image = ctx.app_caches.image_decode.write().entry_encoded_color(
        row_id,
        component,
        slice,
        media_type.as_ref(),
    )?;

    dl_data_ui::image_preview_ui(
        ctx,
        None, // Can't look up annotations for segmentation images
        ui,
        UiLayout::List,
        &dl_log_types::EntityPath::from("redap_thumbnail"),
        &image,
        None,
    );

    Ok(())
}
