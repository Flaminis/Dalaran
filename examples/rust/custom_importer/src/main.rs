//! This example demonstrates how to implement and register a [`dl_importer::Importer`] into
//! the Dalaran Viewer in order to add support for loading arbitrary files.
//!
//! Usage:
//! ```sh
//! $ cargo r -p custom_importer -- path/to/some/file
//! ```

use dalaran::external::{anyhow, dl_build_info, dl_importer, dl_log};
use dalaran::log::{Chunk, RowId};
use dalaran::{EntityPath, ImportedData, Importer as _, TimePoint};

fn main() -> anyhow::Result<std::process::ExitCode> {
    let main_thread_token = dalaran::MainThreadToken::i_promise_i_am_on_the_main_thread();
    dl_log::setup_logging();

    dl_importer::register_custom_importer(HashLoader);

    let build_info = dl_build_info::build_info!();
    dalaran::run(
        main_thread_token,
        build_info,
        dalaran::CallSource::Cli,
        std::env::args(),
    )
    .map(std::process::ExitCode::from)
}

// ---

/// A custom [`dl_importer::Importer`] that logs the hash of file as a [`dalaran::TextDocument`].
struct HashLoader;

impl dl_importer::Importer for HashLoader {
    fn name(&self) -> String {
        "dalaran.importers.HashLoader".into()
    }

    fn import_from_path(
        &self,
        settings: &dalaran::external::dl_importer::ImporterSettings,
        path: std::path::PathBuf,
        tx: crossbeam::channel::Sender<dl_importer::ImportedData>,
    ) -> Result<(), dl_importer::ImporterError> {
        let contents = std::fs::read(&path)?;
        if path.is_dir() {
            return Err(dl_importer::ImporterError::Incompatible(path)); // simply not interested
        }
        hash_and_log(settings, &tx, &path, &contents)
    }

    fn import_from_file_contents(
        &self,
        settings: &dalaran::external::dl_importer::ImporterSettings,
        filepath: std::path::PathBuf,
        contents: std::borrow::Cow<'_, [u8]>,
        tx: crossbeam::channel::Sender<dl_importer::ImportedData>,
    ) -> Result<(), dl_importer::ImporterError> {
        hash_and_log(settings, &tx, &filepath, &contents)
    }
}

fn hash_and_log(
    settings: &dalaran::external::dl_importer::ImporterSettings,
    tx: &crossbeam::channel::Sender<dl_importer::ImportedData>,
    filepath: &std::path::Path,
    contents: &[u8],
) -> Result<(), dl_importer::ImporterError> {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut h = DefaultHasher::new();
    contents.hash(&mut h);

    let doc = dalaran::TextDocument::new(format!("{:08X}", h.finish()))
        .with_media_type(dalaran::MediaType::TEXT);

    let entity_path = EntityPath::from_file_path(filepath);
    let entity_path = format!("{entity_path}/hashed");
    let chunk = Chunk::builder(entity_path)
        .with_archetype(RowId::new(), TimePoint::default(), &doc)
        .build()?;

    let store_id = settings.opened_store_id_or_recommended();
    let data = ImportedData::Chunk(HashLoader::name(&HashLoader), store_id, chunk);
    dl_quota_channel::send_crossbeam(tx, data).ok();

    Ok(())
}
