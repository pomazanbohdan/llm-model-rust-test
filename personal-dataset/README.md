# RustForge Personal Dataset

This directory contains the specification and initial scaffold for a personal Rust dataset designed
to maximize performance on execution-based Rust coding benchmarks.

The dataset is not a "version 2" of an existing public dataset. It is a separate, benchmark-aligned
dataset standard focused on:

- compile correctness
- semantic correctness
- Rust 2024 behavior
- repair and debugging
- async and concurrency
- unsafe and FFI
- macros
- API refactoring
- docs and doctests
- Cargo and workspace tasks

## Layout

```text
personal-dataset/
  README.md
  policy/
  planning/
  schema/
  templates/
  sources/
  splits/
  train/
  dev/
  blind-test/
```

## Core rules

1. Code tasks enter the core dataset only if they pass execution-based validation.
2. Each example must map to at least one benchmark failure mode.
3. Rust edition `2024` is the default target unless a migration task explicitly starts from an older edition.
4. Donor data is accepted only after provenance, license, leakage, and validation review.
5. Failure-driven data collection is part of the dataset lifecycle, not a later add-on.

## First implementation target

The first usable seed of this dataset should contain:

- 2,000 `compile_repair`
- 2,000 `semantic_impl`
- 1,000 `test_driven_bugfix`
- 1,000 `edition2024_migration`
- 1,000 `async_concurrency_fix`
- 1,000 `unsafe_ffi_fix`

Initial target size: 8,000 validated core examples.

## Current status

The repository now contains:

- policy and acceptance rules
- construction principles derived from current code-dataset research
- donor and coverage planning tables
- a first generated `seed` set under `train/seed/`

The generated seed examples are draft candidates and still require execution validation before they can
be promoted into the accepted core train mix.

## Hugging Face publication target

This package is the source of truth for a single publishable Hugging Face dataset artifact:

- one unified export under [hf-dataset](/C:/project/rust-test/hf-dataset)
- ChatML-compatible `messages` rows for Unsloth Studio and Unsloth training flows
- one record carrying both training text and Rust task metadata

Build the final publication package with:

```powershell
.\scripts\build-hf-unified-dataset.ps1
```

## Key files

- criteria: [policy/criteria.md](/C:/project/rust-test/personal-dataset/policy/criteria.md)
- acceptance rules: [policy/acceptance.md](/C:/project/rust-test/personal-dataset/policy/acceptance.md)
- construction principles: [policy/construction-principles.md](/C:/project/rust-test/personal-dataset/policy/construction-principles.md)
- roadmap: [planning/implementation-roadmap.md](/C:/project/rust-test/personal-dataset/planning/implementation-roadmap.md)
- donor review: [planning/donor-matrix.csv](/C:/project/rust-test/personal-dataset/planning/donor-matrix.csv)
- coverage plan: [planning/coverage-matrix.csv](/C:/project/rust-test/personal-dataset/planning/coverage-matrix.csv)
- canonical schema: [schema/example.schema.json](/C:/project/rust-test/personal-dataset/schema/example.schema.json)
- research survey: [sources/research-survey.md](/C:/project/rust-test/personal-dataset/sources/research-survey.md)
