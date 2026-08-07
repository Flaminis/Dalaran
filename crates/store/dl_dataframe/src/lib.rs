//! The Rerun public data APIs. Get dataframes back from your Rerun datastore.

mod engine;
mod query;
pub mod utils;

pub use self::engine::QueryEngine;
#[doc(no_inline)]
pub use self::external::dl_chunk_store::{
    ChunkStoreConfig, ChunkStoreHandle, Index, IndexRange, IndexValue, QueryExpression,
    SparseFillStrategy, ViewContentsSelector,
};
#[doc(no_inline)]
pub use self::external::dl_log_types::{
    AbsoluteTimeRange, EntityPath, EntityPathFilter, EntityPathSubs, ResolvedEntityPathFilter,
    StoreKind, TimeCell, TimeInt, Timeline, TimelineName,
};
#[doc(no_inline)]
pub use self::external::dl_query::{QueryCache, QueryCacheHandle, StorageEngine};
#[doc(no_inline)]
pub use self::external::dl_types_core::{ComponentDescriptor, ComponentType};
pub use self::query::{NextNRowsOutput, QueryHandle};

pub mod external {
    pub use {arrow, dl_chunk, dl_chunk_store, dl_log_types, dl_query, dl_types_core};
}
