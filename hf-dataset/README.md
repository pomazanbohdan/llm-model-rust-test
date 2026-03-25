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
- n<1K
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.jsonl
---

# RustForge Personal Rust Dataset

This repository contains one unified Rust SFT dataset intended for publication on the Hugging Face Hub.

Current version: `0.2.0`

Target Hub repo: `pomazanbohdan/rustforge-personal-rust-dataset`

## Why this format

Hugging Face dataset repositories are loaded from normal data files plus a `README.md` dataset card with YAML metadata.
Unsloth documents ChatML as a common fine-tuning format and shows datasets built from `messages` with `role` and `content` fields.

This export therefore uses a single `train.jsonl` file where each row contains:

- `messages`: ChatML conversation for direct SFT use
- `prompt` and `completion`: convenience columns for non-chat training code
- Rust task metadata, provenance, validation state, and file payloads

## Dataset scope

- compile repair
- semantic implementation
- bugfix
- Rust 2024 migration
- async/concurrency
- unsafe/FFI
- macros
- docs/doctests

## Example loading

```python
from datasets import load_dataset

ds = load_dataset("pomazanbohdan/rustforge-personal-rust-dataset", split="train")
print(ds[0]["messages"])
```

## Unsloth usage

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

If Unsloth Studio asks you to map columns manually, prefer `messages` as the conversation field.
If the UI only supports pairwise instruction data, use `prompt` as the user field and `completion` as the assistant field.

## Important note

This public package is currently generated from internally created seed examples. It is structured correctly for Hugging Face and Unsloth training, but the rows are still marked as draft candidates until they pass the full Rust execution validator.

## Row schema

Each row contains:

- `id`
- `category`
- `difficulty`
- `edition`
- `tier`
- `source_type`, `source_name`, `source_license_status`, `source_leakage_risk`
- `system`, `prompt`, `completion`
- `messages`
- `workspace_files`, `target_files`
- `hidden_file_count`
- `validation`
- `tags`

## Construction

This dataset is exported from the `personal-dataset/` package in the source repository, where the full policy, donor review, schema, and roadmap are tracked.
