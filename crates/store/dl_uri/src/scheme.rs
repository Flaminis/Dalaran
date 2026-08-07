use dl_log::debug_assert;

use crate::Error;

/// The different schemes supported by Dalaran.
///
/// We support `dalaran`, `dalaran+http`, and `dalaran+https`.
/// `dalaran` and `dalaran+https` parses to the same thing, but we prefer to display just `dalaran`.
#[derive(
    Debug, PartialEq, Eq, Copy, Clone, Hash, PartialOrd, Ord, serde::Serialize, serde::Deserialize,
)]
pub enum Scheme {
    DalaranHttp,
    DalaranHttps,
}

impl std::fmt::Display for Scheme {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::DalaranHttp => write!(f, "dalaran+http"),
            Self::DalaranHttps => write!(f, "dalaran"),
        }
    }
}

impl Scheme {
    /// Converts a [`Scheme`] to either `http` or `https`.
    pub(crate) fn as_http_scheme(&self) -> &str {
        match self {
            Self::DalaranHttps => "https",
            Self::DalaranHttp => "http",
        }
    }

    /// Converts a dalaran url into a canonical http or https url.
    pub(crate) fn canonical_url(&self, url: &str) -> String {
        match self {
            Self::DalaranHttp => {
                debug_assert!(url.starts_with("dalaran+http://"));
                url.replace("dalaran+http://", "http://")
            }
            Self::DalaranHttps => {
                if url.starts_with("dalaran://") {
                    url.replace("dalaran://", "https://")
                } else if url.starts_with("dalaran+https://") {
                    url.replace("dalaran+https://", "https://")
                } else {
                    debug_assert!(false, "unexpected url format: {url}");
                    url.to_owned()
                }
            }
        }
    }
}

impl std::str::FromStr for Scheme {
    type Err = Error;

    fn from_str(url: &str) -> Result<Self, Self::Err> {
        if url.starts_with("dalaran+http://") {
            Ok(Self::DalaranHttp)
        } else if url.starts_with("dalaran://") || url.starts_with("dalaran+https://") {
            Ok(Self::DalaranHttps)
        } else {
            Err(crate::Error::InvalidScheme)
        }
    }
}
