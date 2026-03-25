# Research Survey

This file records the current dataset-construction ideas that directly influence the RustForge personal dataset.

## Findings we are applying

### Execution-grounded supervision

Research on code generation and reconstruction tasks consistently points to strong gains when supervision is tied to program behavior and execution rather than text matching alone.

Practical adoption:

- every core Rust code example should include a workspace and validation path
- hidden tests or equivalent behavioral validation should dominate semantic examples

### Verified synthetic generation

Recent work on self-generated code data shows that synthetic examples become valuable when a model generates multiple candidates and only validated ones survive filtering.

Practical adoption:

- synthetic Rust generation is allowed
- validation is mandatory before the example is eligible for the core train mix

### Preference tuning from validated candidates

Modern code datasets increasingly derive preference pairs from validated candidate sets rather than only from human-written comparisons.

Practical adoption:

- collect multiple candidate fixes for the same Rust task
- rank validated candidates by correctness, minimality, idiomaticity, and safety
- use those rankings to form preference pairs

### Strong tests matter as much as example count

Recent benchmark and dataset work stresses that test quality and coverage directly affect the usefulness of code data.

Practical adoption:

- prioritize examples with behavioral tests
- for async and unsafe examples, create tests tailored to lock scope, cancellation, or safety boundaries

### Contamination control and split hygiene

Recent code intelligence work treats contamination and split management as a design requirement, especially for evaluation-oriented datasets.

Practical adoption:

- track provenance
- reject donor sources that are clearly `dev`, `test`, or verified benchmark holdouts
- keep blind splits isolated and versioned

### Deduplication and curation

Current large-scale code dataset curation uses deduplication, repository-level grouping, heuristic filtering, and license awareness.

Practical adoption:

- repository grouping matters for Rust workspace tasks
- donor data should be deduplicated and cleaned before ingestion
- license and opt-out status must be part of donor review

## External references

- Case2Code: <https://arxiv.org/abs/2407.12504>
- SelfCodeAlign: <https://arxiv.org/abs/2410.24198>
- CodeDPO: <https://arxiv.org/abs/2410.05605>
- CLOVER: <https://arxiv.org/abs/2502.08806>
- rStar-Coder: <https://arxiv.org/abs/2505.21297>
- LeetCodeDataset: <https://arxiv.org/abs/2504.14655>
- DePA: <https://arxiv.org/abs/2502.20246>
- Data contamination in code intelligence: <https://arxiv.org/abs/2506.02791>
- The Stack v2 curation: <https://github.com/bigcode-project/the-stack-v2>

## How this changes our dataset

These findings push the personal Rust dataset toward:

- fewer but higher-quality core examples
- benchmark-aligned repair and semantic tasks
- execution-first validation
- preference data generated from verified candidates
- continuous failure-driven expansion

