# Dataset Criteria

## Objective

The dataset must optimize a Rust coding model for real Rust development workflows, not for generic
code-text tasks. Its target is high performance on execution-based evaluation under a current stable
toolchain with Rust edition `2024`.

## Required criteria

### 1. Benchmark alignment

Every example must map to at least one of these benchmark-oriented categories:

- `compile_repair`
- `semantic_impl`
- `test_driven_bugfix`
- `clippy_fmt_cleanup`
- `edition2024_migration`
- `async_concurrency_fix`
- `unsafe_ffi_fix`
- `macro_fix`
- `api_refactor`
- `doctest_doc_fix`

Examples that do not map to benchmark failure modes are auxiliary only.

### 2. Execution grounding

Core code examples must be validated through execution, not just textual review.

Required checks:

- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo test`
- `cargo fmt --check`
- `cargo doc --no-deps`
- `cargo test --doc` when applicable

### 3. Real-work Rust

Examples must resemble real developer tasks:

- implement a function inside an existing crate
- patch a bug with a minimal diff
- migrate code to Rust 2024
- fix async lock misuse
- repair an unsafe or FFI boundary
- fix a doctest or rustdoc failure
- preserve a public API while correcting behavior

### 4. Minimal patch behavior

Repair examples must prefer minimal semantically correct patches over full rewrites.

### 5. Idiomatic Rust

The dataset must reward:

- correct ownership and borrowing
- proper `Result` and `Option` usage
- precise trait bounds
- idiomatic iterator usage
- avoiding unnecessary allocation or clones
- explicit and valid unsafe boundaries

### 6. Rust 2024 specificity

The dataset must explicitly cover Rust 2024 behavior, not only generic Rust:

- temporary scope changes
- RPIT lifetime capture
- unsafe extern blocks
- unsafe attributes
- macro fragment changes
- newly unsafe environment APIs

### 7. Failure-driven updates

The dataset must be expanded continuously from observed benchmark failures:

- compile failures
- semantic test failures
- lint failures
- doc/doctest failures
- edition-specific failures
- async failures
- unsafe failures
- macro failures

### 8. Provenance and legal cleanliness

Each example must record:

- source type
- source dataset or repository
- license status
- transformation history
- validation status
- leakage risk

## Explicit exclusions from the core dataset

These may exist only as low-weight auxiliary data:

- generic naming tasks
- code summarization
- code explanation without execution grounding
- docstring-only tasks
- raw agent traces without gold validated solutions
- benchmark dev/test leakage

