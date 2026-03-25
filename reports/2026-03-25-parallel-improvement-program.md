# Parallel Improvement Program

Date: `2026-03-25`

## Goal

Run dataset improvement as multiple coordinated tracks instead of one long sequential validation loop.

## Tracks

### Track A: Family Stability

Status: completed

- canonical family cascade reached `48/48` passing core families
- all core families now pass `cheap`, `medium`, and `full` gates
- result stored in:
  - [cascade-summary.json](/C:/project/rust-test/hf-dataset/reports/family-cascade/cascade-summary.json)
  - [2026-03-25-hf-dataset-family-cascade-v2.md](/C:/project/rust-test/reports/2026-03-25-hf-dataset-family-cascade-v2.md)

### Track B: Parallel Family-Depth Verification

Status: completed

- new orchestrator: [parallel-improve-hf-dataset.py](/C:/project/rust-test/scripts/parallel-improve-hf-dataset.py)
- run configuration:
  - `validation-tier=full`
  - `window-size=2`
  - `waves=2`
  - `workers=4`
- outcome:
  - `96` family-depth tasks
  - `96` validated
  - `0` failed

Artifacts:

- [parallel-summary.json](/C:/project/rust-test/hf-dataset/reports/parallel-improve/parallel-summary.json)
- [parallel-rows.json](/C:/project/rust-test/hf-dataset/reports/parallel-improve/parallel-rows.json)

Targeted follow-up waves also landed for the highest-value categories:

- `semantic_impl`: `24/24` additional full validations
- `unsafe_ffi_fix`: `15/15` additional full validations
- `cargo_workspace_fix`: `12/12` additional full validations

Artifacts:

- [target-depth-semantic](/C:/project/rust-test/hf-dataset/reports/target-depth-semantic)
- [target-depth-unsafe](/C:/project/rust-test/hf-dataset/reports/target-depth-unsafe)
- [target-depth-cargo](/C:/project/rust-test/hf-dataset/reports/target-depth-cargo)

### Track C: Priority Subset Refresh

Status: completed

- new priority subset: [hf-dataset-priority-v3](/C:/project/rust-test/hf-dataset-priority-v3)
- total rows: `14,995`
- verified core rows: `192`
- stable core rows: `14,053`
- auxiliary rows: `750`

Manifest:

- [manifest.json](/C:/project/rust-test/hf-dataset-priority-v3/manifest.json)

An expanded priority subset is now also available:

- [hf-dataset-priority-v4](/C:/project/rust-test/hf-dataset-priority-v4)
- total rows: `14,995`
- verified core rows: `342`
- stable core rows: `13,903`
- auxiliary rows: `750`

Combined family scoring across all validation artifacts:

- [family-scores-all](/C:/project/rust-test/hf-dataset/reports/family-scores-all)
- unique validated rows tracked: `438`

### Track D: Generator Hardening

Status: completed

- identified a fmt-sensitive edge in `compile_repair.parse_ports_collect` during deeper family windows
- patched [generate-hf-rustforge-50k.py](/C:/project/rust-test/scripts/generate-hf-rustforge-50k.py) to make the target signature length-aware
- regenerated the canonical `hf-dataset` and reran the parallel depth program successfully

## Next Best Steps

1. Expand family-depth validation beyond the first `4` rows per family.
2. Promote `hf-dataset-priority-v4` as the default low-cost training subset.
3. Keep increasing verified depth on `semantic_impl`, `unsafe_ffi_fix`, and `cargo_workspace_fix` before broadening to the remaining core families.
