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

- one record per category
- 13 total records checked

Result:

- skipped auxiliary: `2`
- validated core records: `11`
- failed core records: `0`

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

- verified rows promoted: `11`
- output package: [hf-dataset-verified](/C:/project/rust-test/hf-dataset-verified)

## Next actions

1. keep reducing duplicate pressure, especially inside the large core families
2. run validation on a larger per-category sample instead of only one record per category
3. expand the verified subset from dozens to hundreds and then thousands of rows
4. keep adding real benchmark-failure-driven examples on top of the synthetic base
