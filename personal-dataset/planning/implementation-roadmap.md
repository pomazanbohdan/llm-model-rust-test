# Implementation Roadmap

## Phase 0. Freeze scope

Deliverables:

- `PROJECT_SCOPE.md`
- benchmark category list
- base model list
- inference-time validation policy

Goal:

- define what "100%" means for the target Rust workflow

## Phase 1. Schema and policy

Deliverables:

- canonical example schema
- provenance rules
- split rules
- acceptance policy

Goal:

- make every later example creation step deterministic and reviewable

## Phase 2. Coverage matrix

Deliverables:

- feature coverage matrix
- target counts per task category
- donor mapping per category

Goal:

- know which Rust areas are covered, missing, or overrepresented

## Phase 3. Donor audit

Deliverables:

- donor matrix with status and cleaning rules
- leakage review
- license review

Goal:

- restrict the training mixture to safe and useful donor sources

## Phase 4. Validator tooling

Deliverables:

- workspace materializer
- execution validator
- metadata validator
- split overlap checker

Goal:

- make dataset ingestion reproducible and execution-based

## Phase 5. Seed dataset

Deliverables:

- 8k validated core examples
- train/dev/blind-test split manifests

Goal:

- create the first trainable dataset with strong alignment

## Phase 6. Failure harvesting

Deliverables:

- benchmark failure bucket
- failure taxonomy report
- generated repair templates from observed failures

Goal:

- turn benchmark misses into new high-value training data

## Phase 7. Iterative tuning loop

Deliverables:

- experiment reports
- benchmark deltas
- donor/source effectiveness notes

Goal:

- converge toward high benchmark performance through measured iteration

