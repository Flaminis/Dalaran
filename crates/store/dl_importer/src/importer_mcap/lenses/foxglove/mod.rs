use dl_lenses::{LensBuilderError, Lenses};
use dl_log_types::TimeType;

/// Adds all Foxglove lenses to an existing collection.
pub fn add_foxglove_lenses(
    lenses: Lenses,
    time_type: TimeType,
) -> Result<Lenses, LensBuilderError> {
    Ok(dl_lenses::semantic::foxglove::all(time_type)?
        .into_iter()
        .fold(lenses, Lenses::add_lens))
}
