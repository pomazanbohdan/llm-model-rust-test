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

This is a single unified Rust SFT dataset published for Hugging Face and Unsloth workflows.

Current version: `0.3.0`

Target Hub repo: `pomazanbohdan/rustforge-personal-rust-dataset`

## Scale

- total records: `50,000`
- format: ChatML-style `messages`
- storage: sharded JSONL

## Category mix

| Category | Count |
| --- | ---: |
| compile_repair | 9000 |
| semantic_impl | 9000 |
| test_driven_bugfix | 7000 |
| edition2024_migration | 5000 |
| async_concurrency_fix | 5000 |
| unsafe_ffi_fix | 5000 |
| clippy_fmt_cleanup | 2500 |
| macro_fix | 2500 |
| api_refactor | 1500 |
| doctest_doc_fix | 1000 |
| rust_qa | 1500 |
| review_preference | 1000 |

## Unsloth compatibility

Use `messages` as the conversation field. If a UI asks for manual pairwise mapping, use:

- `prompt` as the user field
- `completion` as the assistant field

```python
from datasets import load_dataset
from unsloth.chat_templates import get_chat_template

dataset = load_dataset("pomazanbohdan/rustforge-personal-rust-dataset", split="train")
tokenizer = get_chat_template(tokenizer, chat_template="chatml")

def formatting_prompts_func(examples):
    texts = [
        tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        for messages in examples["messages"]
    ]
    return {"text": texts}

dataset = dataset.map(formatting_prompts_func, batched=True)
```

## Important note

This 50k release is a synthetic HF-first Rust corpus aligned to the benchmark plan.
Rows remain marked as synthetic candidates until they are execution-validated and promoted into a verified subset.
