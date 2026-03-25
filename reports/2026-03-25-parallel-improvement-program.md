# Parallel Improvement Program

Date: `2026-03-25`

## Goal

Run dataset improvement as multiple coordinated tracks instead of one long sequential validation loop.

## Tracks

## Coverage Expansion

Status: completed

New Rust-specific family coverage added in the latest generator pass:

- `compile_repair.stringify_collect_owned`
- `edition2024_migration.static_mut_once_lock`
- `async_concurrency_fix.watch_shutdown`
- `cargo_workspace_fix.workspace_feature_flag`

Current core coverage baseline:

- `52/52` core families pass `cheap`, `medium`, and `full`
- `edition2024_migration` now covers `6` families
- `async_concurrency_fix` now covers `6` families
- `cargo_workspace_fix` now covers `5` families
- `compile_repair` now covers `5` families

Important generator hardening:

- [generate-hf-rustforge-50k.py](/C:/project/rust-test/scripts/generate-hf-rustforge-50k.py) now preserves `hf-dataset/reports/` during corpus rebuilds instead of deleting local validation history

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

Targeted follow-up waves were then expanded across the full core Rust stack:

- `semantic_impl`: `40/40` additional full validations
- `unsafe_ffi_fix`: `25/25` additional full validations
- `async_concurrency_fix`: `30/30` additional full validations
- `edition2024_migration`: `30/30` additional full validations
- `cargo_workspace_fix`: `25/25` additional full validations
- `compile_repair`: `25/25` additional full validations
- `test_driven_bugfix`: `20/20` additional full validations
- `doctest_doc_fix`: `15/15` additional full validations
- `clippy_fmt_cleanup`: `15/15` additional full validations
- `api_refactor`: `20/20` additional full validations
- `macro_fix`: `15/15` additional full validations

Artifacts:

- [depth-semantic](/C:/project/rust-test/hf-dataset/reports/depth-semantic)
- [depth-unsafe](/C:/project/rust-test/hf-dataset/reports/depth-unsafe)
- [depth-async](/C:/project/rust-test/hf-dataset/reports/depth-async)
- [depth-edition](/C:/project/rust-test/hf-dataset/reports/depth-edition)
- [depth-cargo](/C:/project/rust-test/hf-dataset/reports/depth-cargo)
- [depth-compile](/C:/project/rust-test/hf-dataset/reports/depth-compile)
- [depth-bugfix](/C:/project/rust-test/hf-dataset/reports/depth-bugfix)
- [depth-docs](/C:/project/rust-test/hf-dataset/reports/depth-docs)
- [depth-clippy](/C:/project/rust-test/hf-dataset/reports/depth-clippy)
- [depth-api](/C:/project/rust-test/hf-dataset/reports/depth-api)
- [depth-macro](/C:/project/rust-test/hf-dataset/reports/depth-macro)

Current aggregate quality state:

- [family-scores-all](/C:/project/rust-test/hf-dataset/reports/family-scores-all)
- `2,860` validated rows tracked across all validation artifacts
- `2,756` validated core rows
- `55` validated rows for every one of the `52` core families
- `0` failed rows in the aggregated family score snapshot
- `52` stable core families at the current threshold

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

Latest high-confidence subset after the expanded depth program:

- [hf-dataset-priority-v7](/C:/project/rust-test/hf-dataset-priority-v7)
- total rows: `14,995`
- verified core rows: `572`
- stable core rows: `13,673`
- auxiliary rows: `750`
- threshold used: `13` validated rows per family at `100%` pass rate

Current default high-confidence subset:

- [hf-dataset-priority-v9](/C:/project/rust-test/hf-dataset-priority-v9)
- total rows: `14,995`
- verified core rows: `2,756`
- stable core rows: `11,489`
- auxiliary rows: `750`
- threshold used: `55` validated rows per family at `100%` pass rate

### Track D: Generator Hardening

Status: completed

- identified a fmt-sensitive edge in `compile_repair.parse_ports_collect` during deeper family windows
- patched [generate-hf-rustforge-50k.py](/C:/project/rust-test/scripts/generate-hf-rustforge-50k.py) to make the target signature length-aware
- regenerated the canonical `hf-dataset` and reran the parallel depth program successfully

## Next Best Steps

1. Raise validated depth from `55` to `100+` rows per core family.
2. Promote [hf-dataset-priority-v9](/C:/project/rust-test/hf-dataset-priority-v9) as the default low-cost training subset.
3. Keep growing full validation on `semantic_impl`, `unsafe_ffi_fix`, `async_concurrency_fix`, `edition2024_migration`, and `cargo_workspace_fix`.
4. Refresh the HF dataset card whenever the validated-depth milestone moves materially.
