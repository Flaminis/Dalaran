//! Dalaran gRPC header conventions: the `x-dalaran-*` header consts, the
//! [`DalaranVersionInterceptor`] that stamps every outbound request with the
//! client (or server) identity and version, the matching tower `Layer`
//! helpers that wire it into a stack, and a small fork of
//! `tower-http::propagate_header` used to propagate multiple Dalaran headers
//! between requests and responses.

/// The HTTP header key to pass an entry ID to the `DalaranCloudService` APIs.
pub const DALARAN_HTTP_HEADER_ENTRY_ID: &str = "x-dalaran-entry-id";

/// The HTTP header key to pass an entry name to the `DalaranCloudService` APIs.
///
/// This will automatically be resolved to an entry ID, as long as a dataset with the associated
/// name can be found in the database.
///
/// This is serialized as base64-encoded data (hence `-bin`), since entry names can be any UTF8 strings,
/// while HTTP2 headers only support ASCII.
pub const DALARAN_HTTP_HEADER_ENTRY_NAME: &str = "x-dalaran-entry-name-bin";

/// The HTTP header key that all our official gRPC clients use to specify their identity and version.
///
/// All our official gRPC servers make sure to always return a copy of this header to the client as-is, in
/// addition to propagating it into our gRPC metrics and traces.
pub const DALARAN_HTTP_HEADER_CLIENT_VERSION: &str = "x-dalaran-client-version";

/// The HTTP header key that all our official gRPC servers use to specify their identity and version.
///
/// All our official gRPC servers always set this header in all their responses, in addition to
/// propagating it into our gRPC metrics and traces.
pub const DALARAN_HTTP_HEADER_SERVER_VERSION: &str = "x-dalaran-server-version";

/// HTTP authorization header key, used to transport authorization tokens
pub const HTTP_HEADER_AUTHORIZATION: &str = "authorization";

// ---

pub type DalaranHeadersLayer = tower::layer::util::Stack<
    PropagateHeadersLayer,
    tower::layer::util::Stack<
        tonic::service::InterceptorLayer<DalaranVersionInterceptor>,
        tower::layer::util::Identity,
    >,
>;

/// Instantiates a compound [`tower::Layer`] that handles all things related to Dalaran headers.
pub fn new_dalaran_headers_layer(
    name: Option<String>,
    version: Option<String>,
    is_client: bool,
) -> DalaranHeadersLayer {
    tower::ServiceBuilder::new()
        .layer(tonic::service::interceptor::InterceptorLayer::new({
            DalaranVersionInterceptor::new(is_client, name, version)
        }))
        .layer(new_dalaran_headers_propagation_layer())
        .into_inner()
}

/// Build the standard SDK-side Dalaran headers layer.
///
/// This is the `(name, version, is_client)` triple every Dalaran gRPC client should use
/// unless it has a specific reason not to (e.g. the `redap_cli` binary, which advertises
/// its own `CARGO_PKG_VERSION`). It is the single source of truth for client-side header
/// configuration, so any path that opens a sibling channel (the main redap RPC stack, the
/// per-connection analytics OTLP exports, etc.) presents the same
/// `x-dalaran-client-version` value to the server.
///
/// On wasm, the identity is hard-coded to `"dalaran-web"` so the cloud server can
/// distinguish browser traffic. On native, identity is left to fall through the standard
/// `DalaranVersionInterceptor` chain (`OTEL_SERVICE_NAME` → exe stem → `dl_protos`'s
/// `CARGO_PKG_NAME`) and the version respects `DALARAN_CLIENT_VERSION_OVERRIDE` for tests.
#[cfg(target_arch = "wasm32")]
pub fn new_dalaran_client_headers_layer() -> DalaranHeadersLayer {
    new_dalaran_headers_layer(
        Some("dalaran-web".to_owned()),
        None,
        /* is_client */ true,
    )
}

#[cfg(not(target_arch = "wasm32"))]
pub fn new_dalaran_client_headers_layer() -> DalaranHeadersLayer {
    new_dalaran_headers_layer(
        None,
        std::env::var("DALARAN_CLIENT_VERSION_OVERRIDE").ok(),
        /* is_client */ true,
    )
}

/// Creates a new [`tower::Layer`] middleware that always makes sure to propagate Dalaran headers
/// back and forth across requests and responses.
pub fn new_dalaran_headers_propagation_layer() -> PropagateHeadersLayer {
    PropagateHeadersLayer::new(
        [
            http::HeaderName::from_static(DALARAN_HTTP_HEADER_ENTRY_ID),
            http::HeaderName::from_static(DALARAN_HTTP_HEADER_CLIENT_VERSION),
            http::HeaderName::from_static(DALARAN_HTTP_HEADER_SERVER_VERSION),
        ]
        .into_iter()
        .collect(),
    )
}

/// Implements a `[tonic::service::Interceptor]` that records the identity and version of the client and/or server
/// in well-known headers.
///
/// See also [`DALARAN_HTTP_HEADER_CLIENT_VERSION`] & [`DALARAN_HTTP_HEADER_SERVER_VERSION`].
#[derive(Clone)]
pub struct DalaranVersionInterceptor {
    is_client: bool,
    name: String,
    version: String,
}

impl DalaranVersionInterceptor {
    pub fn new_client(name: Option<String>, version: Option<String>) -> Self {
        Self::new(true, name, version)
    }

    pub fn new_server(name: Option<String>, version: Option<String>) -> Self {
        Self::new(false, name, version)
    }

    pub fn new(is_client: bool, name: Option<String>, version: Option<String>) -> Self {
        let mut name = name
            .or_else(|| std::env::var("OTEL_SERVICE_NAME").ok())
            .or_else(|| {
                let path = std::env::current_exe().ok()?;
                path.file_stem()
                    .map(|stem| stem.to_string_lossy().to_string())
            })
            .unwrap_or_else(|| env!("CARGO_PKG_NAME").to_owned());

        if !name.is_ascii() {
            // Cannot have non ASCII data in HTTP headers.
            name = "<non_ascii_name_redacted>".to_owned();
        }

        let version = version.unwrap_or_else(|| env!("CARGO_PKG_VERSION").to_owned());

        Self {
            is_client,
            name,
            version,
        }
    }
}

impl tonic::service::Interceptor for DalaranVersionInterceptor {
    fn call(&mut self, mut req: tonic::Request<()>) -> tonic::Result<tonic::Request<()>> {
        let Self {
            is_client,
            name,
            version,
        } = self;

        let version = format!("{name}/{version}");

        req.metadata_mut().insert(
            if *is_client {
                DALARAN_HTTP_HEADER_CLIENT_VERSION
            } else {
                DALARAN_HTTP_HEADER_SERVER_VERSION
            },
            version
                .parse()
                .expect("cannot fail, checked in constructor"),
        );

        Ok(req)
    }
}

// ---

// NOTE: This is a fork of <https://docs.rs/tower-http/0.6.6/tower_http/propagate_header/struct.PropagateHeader.html>.
//
// It exists to prevent never-ending chains of generics when propagating multiple headers, e.g.:
// ```
// pub type RedapClientStack =
//     dl_perf_telemetry::external::tower_http::propagate_header::PropagateHeader<
//         dl_perf_telemetry::external::tower_http::propagate_header::PropagateHeader<
//             dl_perf_telemetry::external::tower_http::propagate_header::PropagateHeader<
//                 dl_perf_telemetry::external::tower_http::propagate_header::PropagateHeader<
//                     dl_perf_telemetry::external::tower_http::trace::Trace<
//                         tonic::service::interceptor::InterceptedService<
//                             tonic::service::interceptor::InterceptedService<
//                                 tonic::transport::Channel,
//                                 dl_auth::client::AuthDecorator,
//                             >,
//                             dl_perf_telemetry::TracingInjectorInterceptor,
//                         >,
//                         dl_perf_telemetry::external::tower_http::classify::SharedClassifier<
//                             dl_perf_telemetry::external::tower_http::classify::GrpcErrorsAsFailures,
//                         >,
//                         dl_perf_telemetry::GrpcMakeSpan,
//                     >,
//                 >,
//             >,
//         >,
//     >;
// ```
// which instead becomes this:
// ```
// pub type RedapClientStack =
//     PropagateHeaders<
//         dl_perf_telemetry::external::tower_http::trace::Trace<
//             tonic::service::interceptor::InterceptedService<
//                 tonic::service::interceptor::InterceptedService<
//                     tonic::transport::Channel,
//                     dl_auth::client::AuthDecorator,
//                 >,
//                 dl_perf_telemetry::TracingInjectorInterceptor,
//             >,
//             dl_perf_telemetry::external::tower_http::classify::SharedClassifier<
//                 dl_perf_telemetry::external::tower_http::classify::GrpcErrorsAsFailures,
//             >,
//             dl_perf_telemetry::GrpcMakeSpan,
//         >,
//     >;
// ```

use std::collections::HashSet;
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll, ready};

use http::header::HeaderName;
use http::{HeaderValue, Request, Response};
use pin_project_lite::pin_project;
use tower::Service;
use tower::layer::Layer;

/// Layer that applies [`PropagateHeaders`] which propagates multiple headers at once from requests to responses.
///
/// If the headers are present on the request they'll be applied to the response as well. This could
/// for example be used to propagate headers such as `x-dalaran-entry-id`, `x-dalaran-client-version`, etc.
#[derive(Clone, Debug)]
pub struct PropagateHeadersLayer {
    headers: HashSet<HeaderName>,
}

impl PropagateHeadersLayer {
    /// Create a new [`PropagateHeadersLayer`].
    pub fn new(headers: HashSet<HeaderName>) -> Self {
        Self { headers }
    }
}

impl<S> Layer<S> for PropagateHeadersLayer {
    type Service = PropagateHeaders<S>;

    fn layer(&self, inner: S) -> Self::Service {
        PropagateHeaders {
            inner,
            headers: self.headers.clone(),
        }
    }
}

/// Middleware that propagates multiple headers at once from requests to responses.
///
/// If the headers are present on the request they'll be applied to the response as well. This could
/// for example be used to propagate headers such as `x-dalaran-entry-id`, `x-dalaran-client-version`, etc.
#[derive(Clone, Debug)]
pub struct PropagateHeaders<S> {
    inner: S,
    headers: HashSet<HeaderName>,
}

impl<S> PropagateHeaders<S> {
    /// Create a new [`PropagateHeaders`] that propagates the given header.
    pub fn new(inner: S, headers: HashSet<HeaderName>) -> Self {
        Self { inner, headers }
    }

    /// Returns a new [`Layer`] that wraps services with a `PropagateHeaders` middleware.
    ///
    /// [`Layer`]: tower::layer::Layer
    pub fn layer(headers: HashSet<HeaderName>) -> PropagateHeadersLayer {
        PropagateHeadersLayer::new(headers)
    }
}

impl<ReqBody, ResBody, S> Service<Request<ReqBody>> for PropagateHeaders<S>
where
    S: Service<Request<ReqBody>, Response = Response<ResBody>>,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = ResponseFuture<S::Future>;

    #[inline]
    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, req: Request<ReqBody>) -> Self::Future {
        let headers_and_values = self
            .headers
            .iter()
            .filter_map(|name| {
                req.headers()
                    .get(name)
                    .cloned()
                    .map(|value| (name.clone(), value))
            })
            .collect();

        ResponseFuture {
            future: self.inner.call(req),
            headers_and_values,
        }
    }
}

pin_project! {
    /// Response future for [`PropagateHeaders`].
    #[derive(Debug)]
    pub struct ResponseFuture<F> {
        #[pin]
        future: F,
        headers_and_values: Vec<(HeaderName, HeaderValue)>,
    }
}

impl<F, ResBody, E> Future for ResponseFuture<F>
where
    F: Future<Output = Result<Response<ResBody>, E>>,
{
    type Output = F::Output;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let this = self.project();
        let mut res = ready!(this.future.poll(cx)?);

        for (header, value) in std::mem::take(this.headers_and_values) {
            res.headers_mut().insert(header, value);
        }

        Poll::Ready(Ok(res))
    }
}
