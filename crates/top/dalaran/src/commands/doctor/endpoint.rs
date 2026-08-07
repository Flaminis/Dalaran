//! The endpoint check: is anything actually listening where the user thinks it is?
//!
//! This is deliberately a plain TCP connect rather than a gRPC handshake. What we are diagnosing
//! is "my SDK cannot reach the viewer", which in practice is a firewall, a container port that
//! was never published, or a viewer that is not running - all of which show up at the TCP layer.
//! A full handshake would need a runtime, a timeout policy and error mapping of its own, and would
//! answer a question the user did not ask.

use std::net::{TcpStream, ToSocketAddrs as _};
use std::time::Duration;

use super::report::{Check, Status};

// ---

/// How long to wait for a connection before giving up.
///
/// Matches the default of the Python doctor. Long enough for a busy machine, short enough that a
/// firewalled address does not stall a CI job.
const CONNECT_TIMEOUT: Duration = Duration::from_secs(2);

/// Tries to open a TCP connection to a `dalaran://`-style gRPC endpoint.
pub fn check_endpoint(endpoint: &str) -> Check {
    let check = Check::new("endpoint", Status::Ok, String::new())
        .with_detail("endpoint", endpoint)
        .with_detail("timeout_seconds", CONNECT_TIMEOUT.as_secs());

    let (host, port) = match split_endpoint(endpoint) {
        Ok(host_and_port) => host_and_port,
        Err(err) => {
            // A URL we cannot even parse is a user error, not a diagnosis, so it is a failure:
            // silently reporting "unreachable" for a typo would be actively misleading.
            return check
                .with_status(Status::Fail, format!("{endpoint:?}: {err}"))
                .with_detail("error", err)
                .with_hint(
                    "Endpoints look like `dalaran+http://127.0.0.1:9876/proxy` or `host:port`.",
                );
        }
    };

    let check = check
        .with_detail("host", host.clone())
        .with_detail("port", port);

    let addresses = match (host.as_str(), port).to_socket_addrs() {
        Ok(addresses) => addresses.collect::<Vec<_>>(),
        Err(err) => {
            return check
                .with_status(
                    Status::Warn,
                    format!("{host} does not resolve to an address"),
                )
                .with_detail("error", err.to_string())
                .with_hint("Check the host name, your DNS, and `/etc/hosts`.");
        }
    };

    // A host can resolve to several addresses (IPv6 and IPv4, typically). The server may well be
    // bound to only one of them, so any success is a success.
    let mut last_error = None;
    for address in &addresses {
        match TcpStream::connect_timeout(address, CONNECT_TIMEOUT) {
            Ok(_stream) => {
                return check
                    .with_detail("address", address.to_string())
                    .with_status(Status::Ok, format!("reachable at {host}:{port}"));
            }
            Err(err) => last_error = Some(err.to_string()),
        }
    }

    check
        .with_detail(
            "addresses",
            serde_json::json!(
                addresses
                    .iter()
                    .map(ToString::to_string)
                    .collect::<Vec<_>>()
            ),
        )
        .with_detail("error", last_error)
        .with_status(
            Status::Warn,
            format!("nothing is listening on {host}:{port}"),
        )
        .with_hint(
            "Start a viewer with `dalaran --serve-grpc`, or check that the port is published and \
             not blocked by a firewall.",
        )
}

/// Splits a `dalaran+http://host:port/path` (or plain `host:port`) endpoint into host and port.
///
/// The default port matches the one `dalaran --serve-grpc` binds, so `dalaran://localhost` does
/// the obvious thing.
fn split_endpoint(endpoint: &str) -> Result<(String, u16), String> {
    if let Ok(origin) = endpoint.parse::<dl_uri::Origin>() {
        return Ok((origin.format_host(), origin.port));
    }

    // Not a Dalaran URI; fall back to a bare `host:port`, which is what people actually type.
    let (host, port) = endpoint
        .rsplit_once(':')
        .ok_or_else(|| "expected `host:port` or a `dalaran://` URL".to_owned())?;

    if host.is_empty() {
        return Err("no host name".to_owned());
    }

    let port = port
        .parse::<u16>()
        .map_err(|err| format!("invalid port {port:?}: {err}"))?;

    Ok((host.to_owned(), port))
}

#[cfg(test)]
mod tests {
    use std::net::TcpListener;

    use super::*;

    #[test]
    fn test_splits_dalaran_urls_and_bare_addresses() {
        // The same spelling the Python doctor uses as its default endpoint.
        assert_eq!(
            split_endpoint("dalaran+http://127.0.0.1:9876/proxy").unwrap(),
            ("127.0.0.1".to_owned(), 9876)
        );
        assert_eq!(
            split_endpoint("dalaran+https://example.com:443").unwrap(),
            ("example.com".to_owned(), 443)
        );
        assert_eq!(
            split_endpoint("localhost:1234").unwrap(),
            ("localhost".to_owned(), 1234)
        );
    }

    #[test]
    fn test_rejects_nonsense() {
        assert!(split_endpoint("").is_err());
        assert!(split_endpoint("no-port-here").is_err());
        assert!(split_endpoint("host:not-a-port").is_err());
        assert!(split_endpoint(":9876").is_err());
    }

    #[test]
    fn test_a_listening_socket_is_reachable() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let port = listener.local_addr().unwrap().port();

        let check = check_endpoint(&format!("dalaran+http://127.0.0.1:{port}/proxy"));
        assert_eq!(check.status, Status::Ok, "{}", check.summary);
        assert_eq!(check.details["port"], port);
        assert!(check.summary.contains("reachable"));
    }

    #[test]
    fn test_a_closed_port_only_warns() {
        // Bind, learn the port, then drop the listener so that nothing is listening any more.
        let port = {
            let listener = TcpListener::bind("127.0.0.1:0").unwrap();
            listener.local_addr().unwrap().port()
        };

        let check = check_endpoint(&format!("127.0.0.1:{port}"));
        // A viewer that is simply not running must never fail a CI pipeline.
        assert_eq!(check.status, Status::Warn, "{}", check.summary);
        assert!(check.summary.contains("nothing is listening"));
        assert!(check.hint.is_some());
    }

    #[test]
    fn test_a_malformed_endpoint_is_a_failure() {
        let check = check_endpoint("not an endpoint at all");
        assert_eq!(check.status, Status::Fail);
        assert!(check.hint.is_some());
    }
}
