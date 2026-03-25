# Acceptance Policy

## Core code examples

A code example may enter `train/` only if all rules below are satisfied.

1. The example has a valid metadata record matching the canonical schema.
2. The example belongs to an approved core category.
3. The example has no known overlap with `dev/` or `blind-test/`.
4. The example has valid provenance and a reviewed legal status.
5. The example passes the required toolchain checks:
   - `cargo check`
   - `cargo clippy -- -D warnings`
   - `cargo test`
   - `cargo fmt --check`
   - `cargo doc --no-deps`
   - `cargo test --doc` if relevant
6. The generated target is normalized with `rustfmt`.
7. The example does not introduce hallucinated crates, APIs, or unstable features.
8. If the task is a patch task, the patch scope is limited and public API constraints are preserved.

## Auxiliary examples

Auxiliary examples may enter the dataset only if they are explicitly marked with:

- `tier = auxiliary`
- `weight <= 0.05` within the active train mix

Examples in this tier must still have provenance and license review.

## Donor rejection rules

Reject a donor source if any of the following holds:

- split name indicates `test`, `dev`, or verified benchmark holdout intended for evaluation
- no clear gold answer or validated target exists
- it is primarily an agent trajectory dataset with no execution-verified final patch
- legal status cannot be determined
- examples are mostly outside Rust development tasks

## Validation policy by category

### `compile_repair`
- must pass `check`, `clippy`, `fmt`, `doc`

### `semantic_impl`
- must pass all checks including hidden tests and doctests where applicable

### `test_driven_bugfix`
- must show at least one fail-to-pass behavior

### `edition2024_migration`
- must explicitly target edition `2024`

### `unsafe_ffi_fix`
- must include a `SAFETY:` explanation when unsafe remains

### `async_concurrency_fix`
- should include behavioral tests that capture lock, shutdown, or cancellation behavior

