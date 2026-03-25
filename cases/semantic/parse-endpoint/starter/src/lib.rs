#[derive(Debug, PartialEq, Eq)]
pub struct Endpoint {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, PartialEq, Eq)]
pub enum ParseEndpointError {
    MissingSeparator,
    EmptyHost,
    InvalidPort,
}

/// Parse `host:port` into an [`Endpoint`].
///
/// # Examples
///
/// ```
/// use semantic_parse_endpoint::{Endpoint, parse_endpoint};
///
/// assert_eq!(
///     parse_endpoint(" localhost :8080 ").unwrap(),
///     Endpoint {
///         host: "localhost".to_string(),
///         port: 8080,
///     }
/// );
/// ```
pub fn parse_endpoint(input: &str) -> Result<Endpoint, ParseEndpointError> {
    todo!("Implement a strict parser without external crates")
}

