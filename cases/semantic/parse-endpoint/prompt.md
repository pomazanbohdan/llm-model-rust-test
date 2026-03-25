# Semantic Layer: parse-endpoint

Implement `parse_endpoint`.

Requirements:

- parse inputs in the form `host:port`
- reject missing separators, empty hosts, and invalid ports
- accept port `0`
- trim surrounding ASCII whitespace from the whole input and from the host segment
- keep the public API unchanged
- do not use external crates

