# Rust Model Comparison Report

Date: 2026-03-25

## Overall ranking

1. omnicoder-9b: 92.0/100, 4/6 passed (66.67%)
2. qwen3.5-9b: 89.0/100, 3/6 passed (50.00%)
3. qwen3.5-35b-a3b: 87.5/100, 3/6 passed (50.00%)
4. omnicoder-2-9b: 62.0/100, 2/6 passed (33.33%)
5. omnicoder-9b-strand-rust-v1: 47.0/100, 2/6 passed (33.33%)

## Composite score methodology

- `compile`: 30 points total
- `edition2024`: 30 points total
- `semantic`: 40 points total
- Full pass gets full case credit; partial failures are discounted by failed check severity.
- `fmt`-only failure keeps partial credit; `clippy`-only keeps less; `check/test/doctest` collapses most of the case value.

## Score table

| Model | Score /100 | Passed | Total | Pass rate | Compile | Edition2024 | Semantic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `omnicoder-9b` | 92.00 | 4 | 6 | 66.67% | 2/2 | 2/2 | 0/2 |
| `qwen3.5-9b` | 89.00 | 3 | 6 | 50.00% | 2/2 | 1/2 | 0/2 |
| `qwen3.5-35b-a3b` | 87.50 | 3 | 6 | 50.00% | 2/2 | 1/2 | 0/2 |
| `omnicoder-2-9b` | 62.00 | 2 | 6 | 33.33% | 2/2 | 0/2 | 0/2 |
| `omnicoder-9b-strand-rust-v1` | 47.00 | 2 | 6 | 33.33% | 1/2 | 1/2 | 0/2 |

## Case outcomes

### omnicoder-9b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: pass
- edition2024/unsafe-extern-repair: pass
- semantic/parse-endpoint: fail (`fmt`)
- semantic/unique-words: fail (`fmt`)

### qwen3.5-9b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: fail (`fmt`)
- edition2024/unsafe-extern-repair: pass
- semantic/parse-endpoint: fail (`fmt`)
- semantic/unique-words: fail (`fmt`)

### qwen3.5-35b-a3b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: pass
- edition2024/unsafe-extern-repair: fail (`clippy`)
- semantic/parse-endpoint: fail (`fmt`)
- semantic/unique-words: fail (`fmt`)

### omnicoder-2-9b

- compile/join-label: pass
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: fail (`check`, `clippy`)
- edition2024/unsafe-extern-repair: fail (`clippy`)
- semantic/parse-endpoint: fail (`check`, `clippy`, `test`, `fmt`, `doctest`)
- semantic/unique-words: fail (`fmt`)

### omnicoder-9b-strand-rust-v1

- compile/join-label: fail (`check`, `clippy`)
- compile/repair-push-slug: pass
- edition2024/unsafe-env-bootstrap: pass
- edition2024/unsafe-extern-repair: fail (`clippy`)
- semantic/parse-endpoint: fail (`check`, `clippy`, `test`, `fmt`, `doctest`)
- semantic/unique-words: fail (`check`, `clippy`, `test`, `fmt`, `doctest`)

## Main takeaways

- `omnicoder-9b` remains the strongest model in this benchmark slice by both raw pass rate and weighted score.
- `qwen3.5-9b` and `qwen3.5-35b-a3b` tie on raw pass rate, but the 9B model ranks slightly higher because its edition failure is `fmt`-only, while the 35B-A3B model drops one case on `clippy`.
- All tested models still fail both semantic cases as final passes; this remains the main weakness of the benchmark slice.
- `omnicoder-9b-strand-rust-v1` stays below its base model, which supports the earlier conclusion that the current fine-tune did not improve this evaluation profile.
- A significant share of misses are still workflow-quality misses (`fmt` / `clippy`), not only semantic logic failures.

## Generated artifacts

- comparison json: `model-workspaces/comparisons/comparison.json`
- comparison csv: `model-workspaces/comparisons/comparison.csv`
