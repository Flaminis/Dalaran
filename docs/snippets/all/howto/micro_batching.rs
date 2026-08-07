//! Shows how to configure micro-batching directly from code.
//!
//! Check out <https://dalaran.dev/docs/reference/sdk/micro-batching> for more information.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Equivalent to configuring the following environment:
    // * DALARAN_FLUSH_NUM_BYTES=<+inf>
    // * DALARAN_FLUSH_NUM_ROWS=10
    // * DALARAN_FLUSH_TICK_SECS=10
    let mut config =
        dalaran::log::ChunkBatcherConfig::from_env().unwrap_or_default();
    config.flush_num_bytes = u64::MAX;
    config.flush_num_rows = 10;
    config.flush_tick = std::time::Duration::from_secs(10);

    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_micro_batching")
            .batcher_config(config)
            .spawn()?;

    // These 10 log calls are guaranteed be batched together, and end up in the same chunk.
    for i in 0..10 {
        rec.log("logs", &dalaran::TextLog::new(format!("log #{i}")))?;
    }

    Ok(())
}
