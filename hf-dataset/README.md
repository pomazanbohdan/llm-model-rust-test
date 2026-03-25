---
language:
- en
pretty_name: RustForge Personal Rust Dataset
license: other
task_categories:
- text-generation
tags:
- rust
- code
- synthetic
- instruction
- chatml
- unsloth
- sft
size_categories:
- 10K<n<100K
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*.jsonl
---

# RustForge Personal Rust Dataset

Current version: `0.4.0`

Target Hub repo: `pomazanbohdan/rustforge-personal-rust-dataset`

## Scale

- total records: `50,000`
- format: ChatML-style `messages`
- storage: sharded JSONL

## Category mix

| Category | Count |
| --- | ---: |
| api_refactor | 2000 |
| async_concurrency_fix | 4500 |
| cargo_workspace_fix | 3000 |
| clippy_fmt_cleanup | 2500 |
| compile_repair | 8000 |
| doctest_doc_fix | 1500 |
| edition2024_migration | 5000 |
| macro_fix | 2500 |
| review_preference | 1000 |
| rust_qa | 1000 |
| semantic_impl | 8000 |
| test_driven_bugfix | 6500 |
| unsafe_ffi_fix | 4500 |

## Unsloth compatibility

Use `messages` as the conversation field. If a UI asks for pairwise mapping, use `prompt` and `completion`.
