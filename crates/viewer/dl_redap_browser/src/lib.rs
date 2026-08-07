//! This crates implements the Redap browser feature, including the communication and UI aspects of
//! it.

mod context;
mod entries;
mod folder_card_ui;
mod server_modal;
mod servers;

use std::sync::LazyLock;

use dl_uri::Scheme;
pub use dl_viewer_context::open_url::EXAMPLES_ORIGIN;

pub use self::entries::{Entries, Entry, EntryInner};
pub use self::servers::{Command, RedapServers, Server};

/// Origin used to show the local ui in the redap browser.
///
/// Not actually a valid origin.
pub static LOCAL_ORIGIN: LazyLock<dl_uri::Origin> = LazyLock::new(|| dl_uri::Origin {
    scheme: Scheme::DalaranHttps,
    host: url::Host::Domain(String::from("_local_recordings.dalaran.dev")),
    port: 443,
});

/// Utility function to switch to the examples screen.
pub fn switch_to_welcome_screen(command_sender: &dl_viewer_context::CommandSender) {
    use dl_viewer_context::{SystemCommand, SystemCommandSender as _};

    command_sender.send_system(SystemCommand::SetRoute(
        dl_viewer_context::Route::welcome_page(),
    ));
    command_sender.send_system(SystemCommand::set_selection(
        dl_viewer_context::Item::welcome_page(),
    ));
}
