# Seed Draft Examples

This directory contains the first generated draft examples for the RustForge personal dataset.

Current contents cover these categories:

- `compile_repair`
- `semantic_impl`
- `test_driven_bugfix`
- `edition2024_migration`
- `async_concurrency_fix`
- `unsafe_ffi_fix`
- `macro_fix`
- `doctest_doc_fix`

## Important

These examples are intentionally marked with validation flags set to `false`.

Reason:

- they have been generated and structured according to the dataset schema
- but they have not yet been executed through the full validation pipeline

The next implementation step is to build a validator that materializes each example into a temporary
workspace and runs:

- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo test`
- `cargo fmt --check`
- `cargo doc --no-deps`
- `cargo test --doc`

