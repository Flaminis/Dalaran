//! The in-process "internal catalog" [`dl_server`].
//!
//! The app hosts a single in-process [`dl_server`] (the "internal catalog").
//! The viewer then loads local resources by registering them with that catalog and opening the
//! resulting redap segment URI, instead of importing them directly.
//!
//! The viewer talks to the catalog in-process via [`InternalCatalog::connection`].
//! On native, the same handler is also served on the proxy server's port (see
//! [`InternalCatalog::grpc_service`]) so that other local processes can reach it.
//! The served endpoint is restricted to connections from the local machine.

use std::net::{Ipv4Addr, SocketAddr};
use std::sync::Arc;

use dl_redap_client::Connection;
use dl_server::RerunCloudHandlerBuilder;

#[cfg(not(target_arch = "wasm32"))]
use {
    dl_protos::cloud::v1alpha1::rerun_cloud_service_server::RerunCloudServiceServer,
    dl_server::RerunCloudHandler,
};

/// The in-process internal catalog.
pub struct InternalCatalog {
    /// The origin under which the catalog is registered.
    pub origin: dl_uri::Origin,

    /// The in-process connection the viewer uses to talk to the catalog.
    pub connection: Connection,

    /// The single handler shared between [`Self::connection`] and [`Self::grpc_service`].
    #[cfg(not(target_arch = "wasm32"))]
    handler: Arc<RerunCloudHandler>,
}

impl InternalCatalog {
    /// The catalog as a gRPC service, to be served (loopback-only) on the proxy server's port.
    #[cfg(not(target_arch = "wasm32"))]
    pub fn grpc_service(&self) -> RerunCloudServiceServer<RerunCloudHandler> {
        RerunCloudServiceServer::from_arc(self.handler.clone())
            .max_decoding_message_size(dl_redap_client::MAX_DECODING_MESSAGE_SIZE)
    }
}

/// Build the in-process internal catalog, addressed at the proxy server's port.
#[cfg(not(target_arch = "wasm32"))]
pub fn build(proxy_addr: SocketAddr) -> InternalCatalog {
    let origin = dl_uri::Origin::from_scheme_and_socket_addr(
        dl_uri::Scheme::RerunHttp,
        SocketAddr::from((Ipv4Addr::LOCALHOST, proxy_addr.port())),
    );

    let handler = Arc::new(RerunCloudHandlerBuilder::new().build());
    let connection = Connection::from_service(handler.clone());

    InternalCatalog {
        origin,
        connection,
        handler,
    }
}

/// Build the in-process internal catalog.
#[cfg(target_arch = "wasm32")]
pub fn build() -> InternalCatalog {
    let handler = Arc::new(RerunCloudHandlerBuilder::new().build());
    let connection = Connection::from_service(handler);

    // The Wasm catalog lives purely in-process; the loopback address is a stable identity for the
    // in-memory handler (matching the native construction), not a reachable endpoint.
    let origin = dl_uri::Origin::from_scheme_and_socket_addr(
        dl_uri::Scheme::RerunHttp,
        SocketAddr::from((Ipv4Addr::LOCALHOST, 0)),
    );

    InternalCatalog { origin, connection }
}
