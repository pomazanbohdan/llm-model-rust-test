# Rust 2024 Layer: unsafe-extern-repair

Fix the FFI declaration for Rust 2024.

Requirements:

- keep the public API unchanged
- update the extern block to the Rust 2024 form
- do not wrap safe code in unnecessary unsafe blocks
- keep the crate Clippy-clean

