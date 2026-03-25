# Rust Dataset Gap Analysis

Date: `2026-03-25`

## Goal

Determine whether the current Hugging Face Rust dataset is sufficient to drive the model toward `100%` on the target Rust benchmark suite.

Primary references:

- benchmark definition: [benchmark-plan.md](/C:/project/rust-test/docs/benchmark-plan.md)
- current dataset mix: [task-mix.csv](/C:/project/rust-test/personal-dataset/planning/task-mix.csv)
- current dataset QC: [2026-03-25-hf-dataset-qc.md](/C:/project/rust-test/reports/2026-03-25-hf-dataset-qc.md)

## Executive verdict

Not yet. The current dataset is much stronger and the sampled local validation is now green, but it is still not sufficient to claim real `100%` readiness on the full benchmark.

Main blockers:

1. duplicate pressure in the 50k corpus is still material
2. verified data is still too small relative to the full corpus
3. current validation is still sampled validation, not broad verified coverage
4. important modern Rust surfaces are only partially covered or not covered deeply enough
5. the current benchmark implementation is still only a small Phase 1 slice, while the target benchmark plan is much broader

## Benchmark vs Dataset Matrix

| Benchmark layer | Current dataset coverage | Quality status | Main gaps | Priority |
| --- | --- | --- | --- | --- |
| compile correctness | present via `compile_repair` | medium | too repetitive; limited type/trait/lifetime variety | high |
| semantic correctness | present via `semantic_impl` and `test_driven_bugfix` | medium | weak hidden-test diversity; too many single-function parsers | critical |
| Rust 2024 compatibility | present via `edition2024_migration` | medium | too narrow; currently centered around env mutation and a few edition-style repairs | high |
| async/concurrency | present via `async_concurrency_fix` | medium | mostly lock-scope patterns; missing cancellation, backpressure, shutdown, stream behavior | high |
| unsafe/FFI | present via `unsafe_ffi_fix` | medium | missing deeper soundness cases and richer public safety contracts | critical |
| macros | present via `macro_fix` | medium | mostly declarative macro fragments; missing proc-macro usage and richer hygiene failures | medium |
| API design/refactor | present via `api_refactor` | medium | too shallow; current examples are narrow panic-to-Result rewrites | high |
| migration/repair/review | present via `compile_repair`, `test_driven_bugfix`, `review_preference` | medium | not enough real multi-file patch workflows; weak benchmark-driven repair depth | high |
| docs/doctests | present via `doctest_doc_fix` | medium | missing module-level and feature-gated examples | high |
| Cargo/workspace/tooling | weak | low | almost no workspaces, features, build.rs, resolver, integration layout, multi-crate tasks | critical |

## What the dataset already covers well enough to keep

- compile-repair style Rust tasks
- bugfix/minimal patch framing
- explicit Rust 2024 presence
- async lock-scope repair patterns
- macro fragment and repair direction
- ChatML / Unsloth-ready record structure

These are worth keeping as families, but not in the current repeated volume.

## What is not covered deeply enough

### 1. Semantic depth

The benchmark wants semantic correctness, not only compile success.

Current issue:

- too many records are shallow parser or small function completion tasks
- there are not enough cases with real hidden behavioral variation
- there are not enough multi-branch specs, boundary conditions, integration-style checks, or stateful semantics

Needed expansion:

- multi-case parsers
- iterator/state machine behavior
- collection invariants
- integration test driven mini-crates
- boundary-heavy hidden tests

### 2. Cargo and workspace realism

This is the biggest missing systems layer.

Missing coverage:

- workspaces
- multiple crates
- feature flags
- optional dependencies
- build scripts
- integration test layout
- doctests that depend on crate paths
- package metadata and toolchain interactions

Without this, the dataset is still too snippet-oriented for real Rust project work.

### 3. Modern Rust 2024 breadth

Current coverage includes some edition migration, but not enough of the 2024 surface.

Still missing or weak:

- temporary scope changes beyond simple env patterns
- RPIT lifetime capture
- `unsafe extern` deeper usage
- unsafe attributes breadth
- macro fragment migration depth
- `static mut` replacement families
- newly unsafe standard library APIs beyond env

### 4. Unsafe correctness

Current unsafe block is too weak for a “modern Rust specialist” target.

Missing coverage:

- null handling contracts
- explicit unsafe public API design
- `MaybeUninit`
- slice/raw pointer boundaries
- `Send` / `Sync` invariants
- aliasing assumptions
- ownership transfer over FFI
- callback safety
- soundness review pairs

### 5. Async ecosystem realism

Current async family mostly checks “don’t await while holding a lock”.

Still missing:

- cancellation-safe loops
- timeouts and retries
- bounded channels and backpressure
- graceful shutdown
- stream processing
- select-style coordination
- duplicate work suppression
- lock ordering and starvation cases

### 6. API and library ergonomics

Current API refactor data is too narrow to teach strong library design.

Still missing:

- trait bound design
- zero-copy APIs
- `Cow` / borrowed-return design
- builder ergonomics across multiple fields
- custom error hierarchies
- generic public APIs
- `impl Trait` return ergonomics
- public API docs that compile

### 7. Docs and doctests

The sample validation already showed this is not stable.

Missing coverage:

- crate-qualified examples
- module-level examples
- generic type examples
- failure-to-compile docs fixes
- examples with imports/features

## Quality gaps independent of coverage

These are as important as the missing topics.

### Duplication

From [QC report](/C:/project/rust-test/reports/2026-03-25-hf-dataset-qc.md):

- `50,000` total records
- `42,425` unique semantic keys
- `15,150` records fall into duplicate groups

This is much better than the initial 50k draft, but it still leaves enough repetition to matter for fine-tuning quality.

### Verified subset is still small relative to corpus size

`110` rows were promoted into the base verified subset, and `550` rows now pass the expanded rolling validation subset.

That is enough to prove the strengthen pipeline works and the first rolling slices of the core families are stable, but it is still not enough to anchor the entire 50k corpus by verified rows alone.

### Validation depth is still sampled

The latest sampled validation now passes at `10/10` per core category, and the first `50` rows per core category also pass under the rolling validator. That is a real improvement and a meaningful local milestone.

But it is still sampled validation, not broad verified coverage across the whole corpus.

## Gap by benchmark target volume

The benchmark plan targets `450` evaluation cases across many layers.

To have a realistic chance at `100%`, the train dataset should not just contain category labels matching those layers. It should contain:

- enough variation per layer
- multiple subfamilies per layer
- enough verified examples per subfamily

Current state:

- coverage exists at category level
- coverage is weak at subfeature level
- coverage is weak at multi-file/project level
- verified depth is far below what would be needed

## What must be added for a serious path toward 100%

### Critical additions

1. workspace and multi-crate Cargo tasks
2. higher-diversity semantic tasks with real hidden-test structure
3. stronger unsafe/FFI families
4. stronger doctest/doc families
5. broader Rust 2024 migration families
6. richer async behavior families

### Critical quality improvements

1. reduce duplicate rate radically
2. move from synthetic-only scale to verified scale
3. fix all current failing template families
4. add benchmark-failure-driven generation instead of only template fan-out

## Recommended next build target

Do not expand the current generator to even more rows.

Instead:

1. rebuild generator diversity until duplicate rate is acceptable
2. raise validated sample pass rate across all categories
3. add missing Cargo/workspace and richer semantic families
4. target a smaller but stronger milestone:

- `10k` to `15k` high-diversity rows
- `1k+` verified rows
- full pass on sampled validation for every core category

After that, scale again toward a stronger `50k` release.

## Final answer

The current dataset now reaches `100%` on the latest sampled local validation slice for the core categories, but it still does not justify expecting real `100%` benchmark performance across the full suite.

It is now a strong infrastructure milestone and a usable HF training corpus, but not yet a final Rust-specialist corpus proven at full-benchmark depth.
