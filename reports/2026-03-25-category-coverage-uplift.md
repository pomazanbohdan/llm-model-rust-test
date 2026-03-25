# Rust Dataset Category Coverage Uplift

Date: 2026-03-25

## Goal

Raise every dataset category that was below `50%` ideality coverage to at least `50%`, while minimizing validation cost and preserving stability.

## External guidance used

- Execution-grounded code data remains the strongest signal for code correctness, especially when validation is tied to tests or observable behavior: [Case2Code](https://arxiv.org/abs/2407.12504)
- Synthetic code data is most effective when kept only after sandbox verification, not by raw generation volume alone: [SelfCodeAlign](https://arxiv.org/abs/2410.24198)
- Test quality and targeted verification matter directly for downstream code-model quality, so validation effort should be concentrated where it changes evaluation accuracy: [CodeContests+](https://arxiv.org/abs/2506.05817)

These findings support a low-cost strategy:

1. use a cheap bulk validation tier for large stable families
2. keep a smaller full-validation tail for deeper confidence
3. apply category-appropriate validation to auxiliary data instead of forcing every row through Cargo

## Implementation

New automation added:

- [raise-hf-category-coverage.py](/C:/project/rust-test/scripts/raise-hf-category-coverage.py)
- [validate-hf-auxiliary.py](/C:/project/rust-test/scripts/validate-hf-auxiliary.py)

The uplift runner:

- reads current family scores
- computes the minimum per-family target needed to reach `50%` category coverage
- runs `cheap` validation in bulk for execution categories
- runs a thin `full` tail after the cheap bulk
- runs schema/content validation for auxiliary categories

Output reports were written to:

- [coverage-uplift](/C:/project/rust-test/hf-dataset/reports/coverage-uplift)

## Results

| Category | Validated | Total | Coverage | Stability |
| --- | ---: | ---: | ---: | ---: |
| `api_refactor` | 1,156 | 2,000 | 57.80% | 100% |
| `async_concurrency_fix` | 2,250 | 4,500 | 50.00% | 100% |
| `cargo_workspace_fix` | 1,500 | 3,000 | 50.00% | 100% |
| `clippy_fmt_cleanup` | 1,251 | 2,500 | 50.04% | 100% |
| `compile_repair` | 4,000 | 8,000 | 50.00% | 100% |
| `doctest_doc_fix` | 867 | 1,500 | 57.80% | 100% |
| `edition2024_migration` | 2,502 | 5,000 | 50.04% | 100% |
| `macro_fix` | 1,251 | 2,500 | 50.04% | 100% |
| `review_preference` | 500 | 1,000 | 50.00% | 100% |
| `rust_qa` | 501 | 1,000 | 50.10% | 100% |
| `semantic_impl` | 4,000 | 8,000 | 50.00% | 100% |
| `test_driven_bugfix` | 3,252 | 6,500 | 50.03% | 100% |
| `unsafe_ffi_fix` | 2,250 | 4,500 | 50.00% | 100% |

## Global state after uplift

- total validated rows: `25,280`
- total failed rows: `0`
- stable families: `56/56`
- categories at `50%+`: `13/13`

## Notes

- `review_preference` and `rust_qa` now count toward category ideality through auxiliary schema/content validation rather than Cargo execution.
- The recommended low-cost training subset remains [hf-dataset-priority-v12](/C:/project/rust-test/hf-dataset-priority-v12), because the global minimum validated depth per family is still driven by the untouched `289`-depth families.
- The next quality gain should come from raising the minimum family depth ceiling, not from another broad category uplift.
