# HF Dataset Family Cascade V2

Date: `2026-03-25`

## Outcome

The canonical dataset now passes the family-first validation cascade across all expanded core families.

- core family count: `48`
- cheap tier: `48/48`
- medium tier: `48/48`
- full tier: `48/48`

This means every tracked core family currently passes:

- `cargo check`
- `cargo fmt --check`
- `cargo clippy -- -D warnings`
- `cargo test --no-run`
- `cargo doc --no-deps`
- `cargo test --doc`

using the current cascade sampling configuration of `1` record per family per tier.

## Pipeline Improvements

This milestone required two structural improvements:

1. The generator was expanded from `24` to `48` core families.
2. Family-level validation was fixed to limit by family rather than by category, so targeted validation no longer skipped later families in the same category.

Updated scripts:

- [validate-hf-dataset.py](/C:/project/rust-test/scripts/validate-hf-dataset.py)
- [cascade-hf-validation.py](/C:/project/rust-test/scripts/cascade-hf-validation.py)
- [score-hf-families.py](/C:/project/rust-test/scripts/score-hf-families.py)
- [build-priority-train.py](/C:/project/rust-test/scripts/build-priority-train.py)

## Priority Train V2

Built a refreshed priority subset from the new family-cascade validation artifacts:

- output: [hf-dataset-priority-v2](/C:/project/rust-test/hf-dataset-priority-v2)
- total rows: `14,995`
- verified core rows: `48`
- stable synthetic core rows: `14,197`
- auxiliary rows: `750`

Manifest:

- [manifest.json](/C:/project/rust-test/hf-dataset-priority-v2/manifest.json)

## Notes

The family score summary includes `52` families because it also counts auxiliary families, while the cascade target for this milestone is the `48` core families only.
