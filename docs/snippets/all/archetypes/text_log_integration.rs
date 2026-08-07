//! Shows integration of Dalaran's `TextLog` with the native logging interface.

use dalaran::external::log;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new(
        "dalaran_example_text_log_integration",
    )
    .spawn()?;

    // Log a text entry directly:
    rec.log(
        "logs",
        &dalaran::TextLog::new("this entry has loglevel TRACE")
            .with_level(dalaran::TextLogLevel::TRACE),
    )?;

    // Or log via a logging handler:
    dalaran::Logger::new(rec.clone()) // recording streams are ref-counted
        .with_path_prefix("logs/handler")
        // You can also use the standard `RUST_LOG` environment variable!
        .with_filter(dalaran::default_log_filter())
        .init()?;
    log::info!(
        "This INFO log got added through the standard logging interface"
    );

    log::logger().flush();

    Ok(())
}
