use std::net::{Ipv4Addr, SocketAddr, SocketAddrV4};

use dl_grpc_server::{DEFAULT_SERVER_PORT, ServerOptions, serve, shutdown};

#[tokio::main(flavor = "current_thread")]
async fn main() -> anyhow::Result<()> {
    dl_log::setup_logging();

    serve(
        SocketAddr::V4(SocketAddrV4::new(
            Ipv4Addr::UNSPECIFIED,
            DEFAULT_SERVER_PORT,
        )),
        ServerOptions {
            playback_behavior: dl_grpc_server::PlaybackBehavior::OldestFirst,
            memory_limit: dl_grpc_server::MemoryLimit::from_fraction_of_total(0.75),
            cors_allowed_origins: vec![],
        },
        shutdown::never(),
    )
    .await?;

    Ok(())
}
