use semantic_parse_endpoint::{Endpoint, ParseEndpointError, parse_endpoint};

#[test]
fn parses_valid_endpoint() {
    let endpoint = parse_endpoint("127.0.0.1:3000").unwrap();
    assert_eq!(
        endpoint,
        Endpoint {
            host: "127.0.0.1".to_string(),
            port: 3000,
        }
    );
}

#[test]
fn trims_outer_and_host_whitespace() {
    let endpoint = parse_endpoint("  api.internal :42 ").unwrap();
    assert_eq!(
        endpoint,
        Endpoint {
            host: "api.internal".to_string(),
            port: 42,
        }
    );
}

#[test]
fn accepts_zero_port() {
    let endpoint = parse_endpoint("localhost:0").unwrap();
    assert_eq!(endpoint.port, 0);
}

#[test]
fn rejects_empty_host() {
    let error = parse_endpoint("   :8080").unwrap_err();
    assert_eq!(error, ParseEndpointError::EmptyHost);
}

#[test]
fn rejects_missing_separator() {
    let error = parse_endpoint("localhost").unwrap_err();
    assert_eq!(error, ParseEndpointError::MissingSeparator);
}

#[test]
fn rejects_invalid_port() {
    let error = parse_endpoint("localhost:99999").unwrap_err();
    assert_eq!(error, ParseEndpointError::InvalidPort);
}

