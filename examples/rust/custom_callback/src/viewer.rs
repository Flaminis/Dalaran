use custom_callback::comms::viewer::ControlViewer;
use custom_callback::panel::Control;
use rerun::external::{eframe, dl_crash_handler, dl_grpc_server, dl_log, dl_memory, dl_viewer};

// By using `dl_memory::AccountingAllocator` Rerun can keep track of exactly how much memory it is using,
// and prune the data store when it goes above a certain limit.
// By using `mimalloc` we get faster allocations.
#[global_allocator]
static GLOBAL: dl_memory::AccountingAllocator<mimalloc::MiMalloc> =
    dl_memory::AccountingAllocator::new(mimalloc::MiMalloc);

/// Port used for control messages
const CONTROL_PORT: u16 = 8888;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let main_thread_token = dl_viewer::MainThreadToken::i_promise_i_am_on_the_main_thread();
    // Direct calls using the `log` crate to stderr. Control with `RUST_LOG=debug` etc.
    dl_log::setup_logging();

    // Install handlers for panics and crashes that prints to stderr and send
    // them to Rerun analytics (if the `analytics` feature is on in `Cargo.toml`).
    dl_crash_handler::install_crash_handlers(dl_viewer::build_info());

    // Listen for gRPC connections from Rerun's logging SDKs.
    // There are other ways of "feeding" the viewer though - all you need is a `dl_log_channel::LogReceiver`.
    let (rx_log, _grpc_server_handle) = dl_grpc_server::spawn_with_recv(
        "0.0.0.0:9877".parse()?,
        Default::default(),
        dl_grpc_server::shutdown::never(),
    );

    // First we attempt to connect to the external application
    let viewer = ControlViewer::connect(format!("127.0.0.1:{CONTROL_PORT}")).await?;
    let handle = viewer.handle();

    // Spawn the viewer client in a separate task
    tokio::spawn(async move {
        viewer.run().await;
    });

    // Then we start the Rerun viewer
    let mut native_options = dl_viewer::native::eframe_options(None);
    native_options.viewport = native_options
        .viewport
        .with_app_id("rerun_example_custom_callback");

    // This is used for analytics, if the `analytics` feature is on in `Cargo.toml`
    let app_env = dl_viewer::AppEnvironment::Custom("My Custom Callback".to_owned());

    let startup_options = dl_viewer::StartupOptions::default();
    let window_title = "Rerun Control Panel";
    eframe::run_native(
        window_title,
        native_options,
        Box::new(move |cc| {
            dl_viewer::customize_eframe_and_setup_renderer(cc)?;

            let mut rerun_app = dl_viewer::App::new(
                main_thread_token,
                dl_viewer::build_info(),
                app_env,
                startup_options,
                cc,
                None,
                dl_viewer::AsyncRuntimeHandle::from_current_tokio_runtime_or_wasmbindgen()?,
            );

            rerun_app.add_log_receiver(rx_log);

            Ok(Box::new(Control::new(rerun_app, handle)))
        }),
    )?;

    Ok(())
}
