# HF Dataset QC

Date: `2026-03-25`

## Dataset build

- dataset repo: `pomazanbohdan/rustforge-personal-rust-dataset`
- format: ChatML `messages`
- total rows: `50,000`
- shards: `10`

## Dedup result

Source: [dedup-summary.json](/C:/project/rust-test/hf-dataset/reports/dedup/dedup-summary.json)

- total records: `50,000`
- unique semantic keys: `42,425`
- duplicate groups: `7,575`
- duplicate records covered by those groups: `15,150`

Interpretation:

- the current generator is now substantially more diverse than the first 50k draft
- the corpus is much closer to a usable training mix, but duplicate pressure is still non-trivial
- next generator iteration should keep raising diversity while shifting more rows into verified status

## Validation sample

Source: [validation-summary.json](/C:/project/rust-test/hf-dataset/reports/validation/validation-summary.json)

Sample policy:

- ten records per category
- 130 total records checked

Result:

- skipped auxiliary: `20`
- validated core records: `110`
- failed core records: `0`
- skipped infra-blocked core records: `0`
- sampled core pass rate: `100%`

Validated categories:

- `compile_repair`
- `semantic_impl`
- `test_driven_bugfix`
- `edition2024_migration`
- `async_concurrency_fix`
- `unsafe_ffi_fix`
- `clippy_fmt_cleanup`
- `macro_fix`
- `api_refactor`
- `doctest_doc_fix`
- `cargo_workspace_fix`

## Verified subset

Source: [manifest.json](/C:/project/rust-test/hf-dataset-verified/manifest.json)

- verified rows promoted: `110`
- output package: [hf-dataset-verified](/C:/project/rust-test/hf-dataset-verified)

## Expanded verified subset

Source: `hf-dataset/reports/validation-expanded/validation-summary.json`

- rolling windows: `10`
- window size: `10` per core category
- validated core rows across rolling windows: `1100 / 1100`
- expanded verified subset rows: `1100`
- per-core-category verified rows: `100`

## Next actions

1. keep reducing duplicate pressure, especially inside the large core families
2. expand rolling validation beyond the first `100` rows per core category
3. expand the verified subset from `1100` toward a larger multi-thousand verified layer
4. keep adding real benchmark-failure-driven examples on top of the synthetic base
