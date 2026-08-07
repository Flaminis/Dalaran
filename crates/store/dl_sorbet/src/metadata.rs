use std::collections::HashMap;

use arrow::datatypes::Field as ArrowField;

// The following constants are used as metadata keys. See also
// [`dl_types_core::component_descriptor`] for additional constants.

/// The key used to identify the chunk ID in batch-level metadata.
pub const DALARAN_CHUNK_ID: &str = "dalaran:id";

/// The key used to identify the index name in field-level metadata.
pub const SORBET_INDEX_NAME: &str = "dalaran:index_name";

/// The key used to identify the entity path in field-level metadata.
pub const SORBET_ENTITY_PATH: &str = "dalaran:entity_path";

/// The key used to identify the [`crate::column_kind::ColumnKind`] in
/// field-level metadata.
pub const DALARAN_KIND: &str = "dalaran:kind";

/// The key used to identify table columns in the Dalaran server
/// associated as a primary index.
pub const SORBET_IS_TABLE_INDEX: &str = "dalaran:is_table_index";

/// Arrow metadata for an arrow record batch.
pub type ArrowBatchMetadata = HashMap<String, String>;

/// Arrow metadata for a column/field.
pub type ArrowFieldMetadata = HashMap<String, String>;

#[derive(thiserror::Error, Debug)]
#[error("Missing metadata {key:?}")]
pub struct MissingMetadataKey {
    pub key: String,
}

#[derive(thiserror::Error, Debug)]
#[error("Field {field_name:?} is missing metadata {metadata_key:?}")]
pub struct MissingFieldMetadata {
    pub field_name: String,
    pub metadata_key: String,
}

/// The namespace Dalaran writes its Arrow metadata keys under.
pub const DALARAN_METADATA_PREFIX: &str = "dalaran:";

/// The namespace upstream Rerun writes its Arrow metadata keys under.
///
/// Dalaran renamed the prefix when it forked, but the on-disk container is
/// unchanged, so recordings written by upstream still carry `rerun:…` keys. We
/// read both spellings and only ever write [`DALARAN_METADATA_PREFIX`], which is
/// what makes existing `.rrd` files readable rather than merely openable.
pub const LEGACY_RERUN_METADATA_PREFIX: &str = "rerun:";

/// The upstream spelling of a Dalaran metadata key, if it has one.
///
/// ```ignore
/// assert_eq!(legacy_metadata_key("dalaran:id").as_deref(), Some("rerun:id"));
/// assert_eq!(legacy_metadata_key("sorbet:version"), None);
/// ```
pub fn legacy_metadata_key(key: &str) -> Option<String> {
    key.strip_prefix(DALARAN_METADATA_PREFIX)
        .map(|suffix| format!("{LEGACY_RERUN_METADATA_PREFIX}{suffix}"))
}

/// Make it more ergonomic to work with arrow metadata.
pub trait MetadataExt {
    type Error;

    fn missing_key_error(&self, key: &str) -> Self::Error;

    /// Look up exactly this key, with no legacy fallback.
    fn get_opt_raw(&self, key: &str) -> Option<&str>;

    /// Look up a key, falling back to its upstream Rerun spelling.
    ///
    /// This is the reason a recording written by upstream decodes here at all:
    /// its batch and field metadata is namespaced `rerun:…`, and every reader in
    /// the tree goes through this method.
    fn get_opt(&self, key: &str) -> Option<&str> {
        if let Some(value) = self.get_opt_raw(key) {
            return Some(value);
        }
        legacy_metadata_key(key).and_then(|legacy| self.get_opt_raw(&legacy))
    }

    fn get_or_err(&self, key: &str) -> Result<&str, Self::Error> {
        self.get_opt(key).ok_or_else(|| self.missing_key_error(key))
    }

    /// If the key exists and is NOT `false`.
    fn get_bool(&self, key: &str) -> bool {
        self.get_opt(key)
            .map(|value| !matches!(value.to_lowercase().as_str(), "false" | "no"))
            .unwrap_or(false)
    }
}

impl MetadataExt for HashMap<String, String> {
    type Error = MissingMetadataKey;

    fn missing_key_error(&self, key: &str) -> Self::Error {
        MissingMetadataKey {
            key: key.to_owned(),
        }
    }

    fn get_opt_raw(&self, key: &str) -> Option<&str> {
        self.get(key).map(|value| value.as_str())
    }
}

impl MetadataExt for ArrowField {
    type Error = MissingFieldMetadata;

    fn missing_key_error(&self, key: &str) -> Self::Error {
        MissingFieldMetadata {
            field_name: self.name().clone(),
            metadata_key: key.to_owned(),
        }
    }

    fn get_opt_raw(&self, key: &str) -> Option<&str> {
        self.metadata().get(key).map(|v| v.as_str())
    }
}
