# Benchmark Plan

## Layers

The suite is designed around independent evaluation layers:

1. compile correctness
2. semantic correctness
3. Rust 2024 compatibility
4. async and concurrency safety
5. unsafe and FFI correctness
6. macros and proc-macro awareness
7. API design and refactoring
8. migration, repair, and review

## Phase rollout

### Phase 1

- compile correctness
- semantic correctness
- Rust 2024 compatibility

### Phase 2

- async and concurrency
- unsafe and FFI
- migration and repair

### Phase 3

- macros
- API design
- prompt robustness

## Target benchmark volume

- 80 compile-only cases
- 120 semantic cases
- 60 Rust 2024 cases
- 60 async and concurrency cases
- 40 unsafe and FFI cases
- 30 macro cases
- 40 migration and repair cases
- 20 API design and refactor cases

Total target volume: 450 cases

## Metrics

Track at least the following metrics:

- compile rate
- lint-clean rate
- hidden test pass rate
- first-pass success rate
- patch minimality
- Rust 2024 correctness score
- hallucination rate
- idiomaticity score
- unsafe audit score

## Case authoring rules

- use edition `2024` in all starter crates
- keep prompts small and explicit
- keep the starter public and the oracle isolated under `oracle/overlay/`
- prefer hidden tests for semantic tasks
- prefer repair tasks for borrow-checker, migration, and unsafe layers
- tag every case with enough metadata to slice failures later
