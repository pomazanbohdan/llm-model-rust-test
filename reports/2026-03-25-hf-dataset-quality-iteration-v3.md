# HF Dataset Quality Iteration V3

Date: `2026-03-25`

## Summary

This iteration focused on raising overall dataset quality by expanding family diversity and validating new family coverage instead of only increasing raw row count.

## Generator Changes

- upgraded dataset generator to `0.5.0` in [generate-hf-rustforge-50k.py](/C:/project/rust-test/scripts/generate-hf-rustforge-50k.py)
- added explicit `family_id` to generated records
- expanded core family coverage from `24` families to `48` families
- widened generators across:
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

## Diversity Improvement

- previous corpus unique semantic keys: `42,425`
- candidate v3 corpus unique semantic keys: `44,900`
- improvement: `+2,475` unique semantic keys
- duplicate-covered rows dropped from `15,150` to `10,200`

These numbers come from the candidate rebuild in `hf-dataset-next2/`.

## Validation Outcome

Family-first cascade on the expanded family map:

- total core families checked: `48`
- first-pass cheap successes: `43/48`
- first-pass medium successes: `42/43`
- first-pass full successes: `42/42`

The 6 failing families were all localized issues:

- `5` formatting or style-target issues
- `1` missing safety-doc / Clippy issue

All 6 were fixed in the generator after the first cascade:

- `api_refactor.error_enum`
- `async_concurrency_fix.timeout_default`
- `compile_repair.parse_ports_collect`
- `macro_fix.block_capture`
- `test_driven_bugfix.nonempty_lines`
- `edition2024_migration.unsafe_op_in_unsafe_fn`

## Current State

- published canonical dataset remains [hf-dataset](/C:/project/rust-test/hf-dataset)
- improved candidate builds are staged locally in:
  - [hf-dataset-next](/C:/project/rust-test/hf-dataset-next)
  - [hf-dataset-next2](/C:/project/rust-test/hf-dataset-next2)

The canonical folder was not replaced in this pass because a process lock on existing shard files blocked an in-place overwrite on Windows.

## Recommendation

When the lock is cleared, promote `hf-dataset-next2` as the next canonical HF artifact and rerun:

```powershell
python .\scripts\cascade-hf-validation.py --cheap-per-family 1 --medium-per-family 1 --full-per-family 1 --timeout-sec 90
python .\scripts\score-hf-families.py
python .\scripts\optimize-hf-train.py --target-rows 15000 --min-family-validated 20 --min-family-pass-rate 1.0 --aux-share 0.05
```
