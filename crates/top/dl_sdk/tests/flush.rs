use std::time::Duration;

use dl_sdk::RecordingStreamBuilder;

/// Test that we don't block forever when dropping
/// a broken gRPC sink.
#[test]
fn test_drop_grpc_sink() {
    dl_log::setup_logging();
    let url_to_nowhere = "dalaran+http://not.real:1234/proxy";

    dl_log::info!("Connecting…");
    // TODO(emilk): it would be nice to be able to configure `connect_timeout_on_flush` here to speed up this test.
    let rec = RecordingStreamBuilder::new("dalaran_example_grpc_drop_test")
        .connect_grpc_opts(url_to_nowhere)
        .unwrap();

    dl_log::info!("Flushing with timeout…");
    assert!(rec.flush_with_timeout(Duration::from_secs(2)).is_err());

    dl_log::info!("Dropping recording…");
    drop(rec); // If the test hangs here, we have a bug!

    dl_log::info!("Done.");
}
