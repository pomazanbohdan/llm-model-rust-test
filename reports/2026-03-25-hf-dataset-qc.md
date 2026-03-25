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
- unique semantic keys: `5,310`
- duplicate groups: `310`
- duplicate records covered by those groups: `45,000`

Interpretation:

- the current generator produces too many repeated task families
- the 50k corpus is publishable and trainable, but it is not yet high-quality enough to be treated as a final deduplicated release
- next generator iteration must increase template diversity before expanding verified coverage

## Validation sample

Source: [validation-summary.json](/C:/project/rust-test/hf-dataset/reports/validation/validation-summary.json)

Sample policy:

- one record per category
- 12 total records checked

Result:

- skipped auxiliary: `2`
- validated core records: `6`
- failed core records: `4`

Validated categories:

- `compile_repair`
- `test_driven_bugfix`
- `edition2024_migration`
- `async_concurrency_fix`
- `clippy_fmt_cleanup`
- `macro_fix`

Failed categories:

- `semantic_impl`: `fmt` failure
- `unsafe_ffi_fix`: clippy failure `not_unsafe_ptr_arg_deref`
- `api_refactor`: `fmt` failure and a Windows Application Control test-exec block
- `doctest_doc_fix`: doctest import failure

## Verified subset

Source: [manifest.json](/C:/project/rust-test/hf-dataset-verified/manifest.json)

- verified rows promoted: `6`
- output package: [hf-dataset-verified](/C:/project/rust-test/hf-dataset-verified)

## Next actions

1. diversify generators before the next large rebuild
2. fix failing templates in `semantic_impl`, `unsafe_ffi_fix`, `api_refactor`, `doctest_doc_fix`
3. rerun validation on a larger per-category sample
4. publish a deduplicated verified release after generator v2
