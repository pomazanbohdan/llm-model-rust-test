# Current Rust Dataset Diversity

## Snapshot

- canonical dataset: [hf-dataset](/C:/project/rust-test/hf-dataset)
- total records: `56,000`
- unique semantic keys: `55,100`
- duplicate groups: `900`
- duplicate-covered rows: `1,800`
- semantic uniqueness rate: `98.39%`

## Interpretation

The active corpus is now both fully audited and highly diverse:

- only `3.21%` of rows fall into duplicate-covered groups
- duplicate groups are bounded and expected from controlled template variation
- the remaining `98.39%` of rows are unique under the normalized semantic hash used by the dataset pipeline

## Category Counts

| Category | Rows |
| --- | ---: |
| `api_refactor` | 4,000 |
| `async_concurrency_fix` | 6,000 |
| `cargo_workspace_fix` | 5,000 |
| `clippy_fmt_cleanup` | 3,000 |
| `compile_repair` | 5,000 |
| `doctest_doc_fix` | 3,000 |
| `edition2024_migration` | 6,000 |
| `macro_fix` | 3,000 |
| `review_preference` | 1,000 |
| `rust_qa` | 3,000 |
| `semantic_impl` | 8,000 |
| `test_driven_bugfix` | 4,000 |
| `unsafe_ffi_fix` | 5,000 |
