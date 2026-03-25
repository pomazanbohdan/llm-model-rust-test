# Rust Model Comparison Report

Date: 2026-03-25

## Overall ranking

1. omnicoder-9b: 4/6 passed (66.67%)
2. qwen3.5-9b: 3/6 passed (50.00%)
3. omnicoder-2-9b: 2/6 passed (33.33%)
4. omnicoder-9b-strand-rust-v1: 2/6 passed (33.33%)

## Layer summary

- omnicoder-9b
  - compile: 2/2
  - edition2024: 2/2
  - semantic: 0/2
- qwen3.5-9b
  - compile: 2/2
  - edition2024: 1/2
  - semantic: 0/2
- omnicoder-2-9b
  - compile: 2/2
  - edition2024: 0/2
  - semantic: 0/2
- omnicoder-9b-strand-rust-v1
  - compile: 1/2
  - edition2024: 1/2
  - semantic: 0/2

## Case outcomes

### omnicoder-2-9b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: fail (`check`, `clippy`)
- edition2024/unsafe-extern-repair: fail (`clippy`)
- semantic/parse-endpoint: fail (`check`, `clippy`, `test`, `fmt`, `doctest`)
- semantic/unique-words: fail (`fmt`)

### omnicoder-9b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: pass
- edition2024/unsafe-extern-repair: pass
- semantic/parse-endpoint: fail (`fmt`)
- semantic/unique-words: fail (`fmt`)

### omnicoder-9b-strand-rust-v1

- compile/join-label: fail (`check`, `clippy`)
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: pass
- edition2024/unsafe-extern-repair: fail (`clippy`)
- semantic/parse-endpoint: fail (`check`, `clippy`, `test`, `fmt`, `doctest`)
- semantic/unique-words: fail (`check`, `clippy`, `test`, `fmt`, `doctest`)

### qwen3.5-9b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: fail (`fmt`)
- edition2024/unsafe-extern-repair: pass
- semantic/parse-endpoint: fail (`fmt`)
- semantic/unique-words: fail (`fmt`)

## Main takeaways

- omnicoder-9b is the current best model in this benchmark slice.
- All four models failed both semantic cases.
- qwen3.5-9b and omnicoder-9b were close on correctness, but qwen3.5-9b dropped one edition2024 case.
- omnicoder-2-9b and omnicoder-9b-strand-rust-v1 were materially weaker on edition2024 and semantic tasks.
- Several failures were formatting-only (`fmt`), which means part of the gap is workflow quality rather than pure logic.

## Generated artifacts

- comparison json: `model-workspaces/comparisons/comparison.json`
- comparison csv: `model-workspaces/comparisons/comparison.csv`
