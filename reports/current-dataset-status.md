# Current Rust Dataset Status

## Snapshot

- canonical dataset: [hf-dataset](/C:/project/rust-test/hf-dataset)
- recommended low-cost subset: [hf-dataset-priority](/C:/project/rust-test/hf-dataset-priority)
- total dataset rows: `50,000`
- current audited rows on this corpus: `49,968`
- failed audited rows: `0`
- categories at `A` or above by family depth: `13/13`
- stable audited families: `56/56`

## Category Rating

Grade scale:

- `A+`: min family depth `>= 1000`
- `A`: min family depth `800..999`

| Category | Audited rows | Total rows | Min..Max family depth | Grade |
| --- | ---: | ---: | ---: | ---: |
| `api_refactor` | 3,200 | 3,200 | `800..800` | `A` |
| `async_concurrency_fix` | 4,800 | 4,800 | `800..800` | `A` |
| `cargo_workspace_fix` | 4,000 | 4,000 | `800..800` | `A` |
| `clippy_fmt_cleanup` | 2,400 | 2,400 | `800..800` | `A` |
| `compile_repair` | 6,500 | 6,500 | `1300..1300` | `A+` |
| `doctest_doc_fix` | 2,400 | 2,400 | `800..800` | `A` |
| `edition2024_migration` | 4,800 | 4,800 | `800..800` | `A` |
| `macro_fix` | 2,400 | 2,400 | `800..800` | `A` |
| `review_preference` | 800 | 800 | `800..800` | `A` |
| `rust_qa` | 2,400 | 2,400 | `800..800` | `A` |
| `semantic_impl` | 6,784 | 6,800 | `850..850` | `A` |
| `test_driven_bugfix` | 5,494 | 5,500 | `1375..1375` | `A+` |
| `unsafe_ffi_fix` | 3,990 | 4,000 | `800..800` | `A` |

## Current Training Subset

- total rows: `14,993`
- verified core rows: `14,243`
- auxiliary rows: `750`
