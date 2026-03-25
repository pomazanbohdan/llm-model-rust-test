# HF 50K Rollout

This rollout defines the first large Hugging Face publication target for the RustForge dataset.

## Target

- one unified dataset repository on Hugging Face
- 50,000 records in total
- ChatML-compatible `messages` rows
- direct compatibility with Unsloth and Unsloth Studio
- sharded JSONL files instead of thousands of local per-example JSON files

## Distribution

| Category | Count |
| --- | ---: |
| compile_repair | 8,000 |
| semantic_impl | 8,000 |
| test_driven_bugfix | 6,500 |
| edition2024_migration | 5,000 |
| async_concurrency_fix | 4,500 |
| unsafe_ffi_fix | 4,500 |
| clippy_fmt_cleanup | 2,500 |
| macro_fix | 2,500 |
| api_refactor | 2,000 |
| doctest_doc_fix | 1,500 |
| cargo_workspace_fix | 3,000 |
| rust_qa | 1,000 |
| review_preference | 1,000 |

Total: `50,000`

## Build policy

1. Generate the HF artifact directly under `hf-dataset/`.
2. Keep the repository source of truth in scripts, planning, and schema files.
3. Do not materialize 50,000 separate training JSON files under `personal-dataset/train/`.
4. Publish sharded `train-xxxxx-of-yyyyy.jsonl` files to the Hugging Face dataset repo.
5. Keep draft/synthetic status explicit until execution validation promotes records into a verified subset.

## Required output

- `hf-dataset/README.md`
- `hf-dataset/manifest.json`
- `hf-dataset/data/train-*.jsonl`

## Next quality gate

After the 50k corpus is published, the next step is not more raw generation. It is:

- execution validation
- deduplication
- failure harvesting from benchmark misses
- promotion of validated subsets into a verified release
