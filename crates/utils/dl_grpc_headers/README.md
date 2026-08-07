# dl_grpc_headers

Dalaran gRPC header conventions.

Contains the well-known `x-dalaran-*` header names, the `DalaranVersionInterceptor` that stamps every outbound request with the client (or server) identity and version, the matching tower `Layer` helpers that wire it into a stack, and a small fork of `tower-http::propagate_header` used to propagate multiple Dalaran headers between requests and responses.

Everything here is plain `tonic`/`tower`/`http` plumbing — no dalaran-internal types — so it can sit on the `crates/utils` tier and be consumed by any crate that needs the same gRPC header behavior.
