//! Viewer binary to avoid compiling the full dalaran-cli, so we can achieve faster compile times.

#[global_allocator]
static GLOBAL: dl_memory::AccountingAllocator<std::alloc::System> =
    dl_memory::AccountingAllocator::new(std::alloc::System);

#[cfg(not(debug_assertions))]
compile_error!("This binary is for development only. Use `dalaran-cli` for production.");

#[cfg(not(target_arch = "wasm32"))]
fn main() -> eframe::Result {
    dl_log::setup_logging();

    let main_thread_token = dl_viewer::MainThreadToken::i_promise_i_am_on_the_main_thread();
    let runtime = tokio::runtime::Runtime::new() // NOLINT: the standalone development viewer owns this runtime
        .expect("failed to create tokio runtime");
    let _tokio_guard = runtime.enter();
    let runtime_handle = dl_viewer::AsyncRuntimeHandle::new_native(runtime.handle().clone());
    let startup_options = dl_viewer::StartupOptions::default();

    dl_viewer::run_native_app(
        main_thread_token,
        Box::new(move |cc| {
            let app = dl_viewer::App::new(
                main_thread_token,
                dl_build_info::build_info!(),
                dl_viewer::AppEnvironment::Custom("example".to_owned()),
                startup_options,
                cc,
                None,
                runtime_handle,
            );
            Ok(Box::new(app))
        }),
        None,
    )
}

#[cfg(target_arch = "wasm32")]
fn main() {
    panic!("This binary is native-only. It cannot be compiled for wasm.");
}
