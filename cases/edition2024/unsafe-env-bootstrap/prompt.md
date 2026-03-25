# Rust 2024 Layer: unsafe-env-bootstrap

Fix the crate for Rust 2024.

Context:

- the function is only called during single-threaded process bootstrap
- no threads are spawned before or during this call

Requirements:

- keep the public API unchanged
- make the Rust 2024 unsafe requirement explicit
- add a precise `// SAFETY:` explanation for the unsafe block
- do not add external dependencies

