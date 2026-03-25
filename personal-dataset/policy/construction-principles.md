# Dataset Construction Principles

This document translates current code-dataset research into operational rules for the RustForge personal dataset.

## Principle 1. Execution beats text similarity

For code tasks, execution-verified supervision is higher value than plain instruction-response text pairs.

Operational rule:

- the dominant train signal must come from examples with runnable workspaces and executable validation
- instruction-only Rust examples are auxiliary, not core

## Principle 2. Verified synthetic data is acceptable

Synthetic data is useful only when generation is followed by sandbox validation and aggressive filtering.

Operational rule:

- synthetic code examples must be generated with multiple candidates
- only candidates that satisfy validation gates may proceed into the candidate pool
- preference data may be built between multiple validated candidates

## Principle 3. Test quality is a first-class asset

Weak tests create weak labels.

Operational rule:

- every semantic example should have hidden tests or equivalently strong behavioral checks
- async and unsafe examples require domain-specific tests, not just happy-path assertions
- benchmark-aligned tests are higher value than generic unit tests

## Principle 4. Dedup and contamination control are mandatory

Large code datasets now treat deduplication, opt-out handling, split hygiene, and contamination review as standard hygiene.

Operational rule:

- keep provenance for every example
- keep split manifests under version control
- reject donor data with explicit dev/test/verified benchmark semantics from training
- deduplicate at repository, template, and example levels where practical

## Principle 5. Preference data should target real quality differences

The dataset should teach the model not only to be correct, but to choose better Rust when more than one correct answer exists.

Operational rule:

- generate preference pairs for minimal patches, idiomatic iterator use, error handling, and unsafe boundaries
- build preference examples from validated candidate sets, not arbitrary model outputs

## Principle 6. Failure harvesting is part of training data generation

The benchmark is not just an evaluator. It is a generator of high-value new examples.

Operational rule:

- collect failed model outputs from benchmark runs
- classify them by failure mode
- convert common failure patterns into new repair or preference tasks

## Principle 7. Temporal and benchmark-safe splits matter

Code datasets are now expected to manage contamination risk explicitly.

Operational rule:

- keep `blind-test` fully isolated
- prevent donor ingestion from benchmark dev/test sets
- avoid exact overlap in crate family, patch, or task template between train and blind-test when possible

## Principle 8. Rust specialization must include tooling

A Rust-specific dataset is incomplete if it ignores Cargo, rustdoc, doctests, clippy, and edition behavior.

Operational rule:

- treat `cargo`, `clippy`, `fmt`, `doc`, and `doctest` as part of the training target
- include Cargo workspaces, feature flags, and documentation examples in the task mix

