//! This example shows how to wrap the Dalaran Viewer in your own GUI.

use std::rc::Rc;
use std::sync::Arc;

use dalaran::external::parking_lot::Mutex;
use dalaran::external::dl_viewer::{self, ViewerEvent, ViewerEventKind};
use dalaran::external::{eframe, egui, dl_crash_handler, dl_grpc_server, dl_log, dl_memory, tokio};

// By using `dl_memory::AccountingAllocator` Dalaran can keep track of exactly how much memory it is using,
// and prune the data store when it goes above a certain limit.
// By using `mimalloc` we get faster allocations.
#[global_allocator]
static GLOBAL: dl_memory::AccountingAllocator<mimalloc::MiMalloc> =
    dl_memory::AccountingAllocator::new(mimalloc::MiMalloc);

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let main_thread_token = dl_viewer::MainThreadToken::i_promise_i_am_on_the_main_thread();

    // Direct calls using the `log` crate to stderr. Control with `RUST_LOG=debug` etc.
    dl_log::setup_logging();

    // Install handlers for panics and crashes that prints to stderr and send
    // them to Dalaran analytics (if the `analytics` feature is on in `Cargo.toml`).
    dl_crash_handler::install_crash_handlers(dl_viewer::build_info());

    // Listen for gRPC connections from Dalaran's logging SDKs.
    // There are other ways of "feeding" the viewer though - all you need is a `dl_log_channel::LogReceiver`.
    let (rx, _grpc_server_handle) = dl_grpc_server::spawn_with_recv(
        "0.0.0.0:9876".parse()?,
        Default::default(),
        dl_grpc_server::shutdown::never(),
    );

    let mut native_options = dl_viewer::native::eframe_options(None);
    native_options.viewport = native_options
        .viewport
        .with_app_id("dalaran_extend_viewer_ui_example");

    let shared_state: Arc<Mutex<SharedState>> = Default::default();

    let startup_options = dl_viewer::StartupOptions {
        on_event: Some({
            let shared_state = shared_state.clone();
            Rc::new(move |event: ViewerEvent| {
                let mut shared_state = shared_state.lock();
                match event.kind {
                    ViewerEventKind::Play | ViewerEventKind::Pause => {}
                    ViewerEventKind::TimeUpdate { time } => {
                        shared_state.current_time = time.as_f64();
                    }
                    ViewerEventKind::TimelineChange {
                        timeline_name,
                        time,
                    } => {
                        shared_state.current_timeline = timeline_name.as_str().to_owned();
                        shared_state.current_time = time.as_f64();
                    }
                    ViewerEventKind::SelectionChange { items } => {
                        shared_state.current_selection = items;
                    }
                    ViewerEventKind::RecordingOpen { .. } => {}
                }
            })
        }),
        ..Default::default()
    };

    // This is used for analytics, if the `analytics` feature is on in `Cargo.toml`
    let app_env = dl_viewer::AppEnvironment::Custom("My Wrapper".to_owned());

    let window_title = "My Customized Viewer";
    eframe::run_native(
        window_title,
        native_options,
        Box::new(move |cc| {
            dl_viewer::customize_eframe_and_setup_renderer(cc)?;

            let mut dalaran_app = dl_viewer::App::new(
                main_thread_token,
                dl_viewer::build_info(),
                app_env,
                startup_options,
                cc,
                None,
                dl_viewer::AsyncRuntimeHandle::from_current_tokio_runtime_or_wasmbindgen()?,
            );
            dalaran_app.add_log_receiver(rx);
            Ok(Box::new(MyApp {
                dalaran_app,
                shared_state,
            }))
        }),
    )?;

    Ok(())
}

#[derive(Default)]
struct SharedState {
    current_selection: Vec<dl_viewer::event::SelectionChangeItem>,
    current_time: f64,
    current_timeline: String,
}

struct MyApp {
    dalaran_app: dl_viewer::App,
    shared_state: Arc<Mutex<SharedState>>,
}

impl eframe::App for MyApp {
    fn save(&mut self, storage: &mut dyn eframe::Storage) {
        // Store viewer state on disk
        self.dalaran_app.save(storage);
    }

    /// Called whenever we need repainting, which could be 60 Hz.
    fn ui(&mut self, ui: &mut egui::Ui, frame: &mut eframe::Frame) {
        // First add our panel(s):
        egui::Panel::right("my_side_panel")
            .default_size(200.0)
            .show(ui, |ui| {
                self.ui(ui);
            });

        // Now show the Dalaran Viewer in the remaining space:
        self.dalaran_app.ui(ui, frame);
    }
}

impl MyApp {
    fn ui(&mut self, ui: &mut egui::Ui) {
        ui.add_space(4.0);
        ui.vertical_centered(|ui| {
            ui.strong("My custom panel");
        });
        ui.separator();

        {
            let shared_state = self.shared_state.lock();

            ui.vertical(|ui| {
                for item in &shared_state.current_selection {
                    selection_item_ui(ui, item);
                }

                ui.separator();

                ui.label(format!(
                    "Current timeline: {}",
                    shared_state.current_timeline
                ));
                ui.label(format!("Current time: {}", shared_state.current_time));
            });
        }
    }
}

fn selection_item_ui(ui: &mut egui::Ui, item: &dl_viewer::SelectionChangeItem) {
    match item {
        dl_viewer::SelectionChangeItem::Entity {
            entity_path,
            instance_id,
            view_name,
            position,
        } => {
            ui.vertical(|ui| {
                if let Some(instance_id) = instance_id.specific_index().map(|id| id.get()) {
                    ui.label(format!("Entity {entity_path}[{instance_id}]"));
                } else {
                    ui.label(format!("Entity {entity_path}"));
                }
                ui.horizontal(|ui| {
                    ui.add_space(16.0);
                    ui.label(format!(
                        "View name: {}",
                        view_name.as_deref().unwrap_or("<unnamed>")
                    ));
                });
                ui.horizontal(|ui| {
                    ui.add_space(16.0);
                    ui.label(position.map_or_else(
                        || "Position: <unknown>".to_owned(),
                        |position| {
                            format!("Position: [{}, {}, {}]", position.x, position.y, position.z)
                        },
                    ));
                });
            });
        }
        dl_viewer::SelectionChangeItem::View { view_id, view_name } => {
            ui.label(format!("View {view_name}"));
            ui.horizontal(|ui| {
                ui.add_space(16.0);
                ui.label(format!("View ID: {}", view_id.uuid()));
            });
        }
        dl_viewer::SelectionChangeItem::Container {
            container_id,
            container_name,
        } => {
            ui.label(format!("Container {container_name}"));
            ui.horizontal(|ui| {
                ui.add_space(16.0);
                ui.label(format!("Container ID: {}", container_id.uuid()));
            });
        }
    }
}
