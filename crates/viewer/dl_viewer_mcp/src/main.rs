//! `re-viewer-mcp` — the standalone binary for the [`dl_viewer_mcp`] MCP server.
//!
//! Mostly useful for dalaran developers. Usually it's recommended to use `dalaran viewer-mcp` instead.

fn main() -> anyhow::Result<()> {
    dl_log::setup_logging();
    let rt = tokio::runtime::Builder::new_multi_thread() // NOLINT: the standalone process owns this runtime
        .enable_all()
        .build()?;
    rt.block_on(dl_viewer_mcp::serve())
}
