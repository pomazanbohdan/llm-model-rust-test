# Current Rust Model Comparison

## Score Table

| Model | Score /100 | Passed | Total | Pass rate | Compile | Edition2024 | Semantic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `omnicoder-9b` | 92.00 | 4 | 6 | 66.67% | 2/2 | 2/2 | 0/2 |
| `qwen3.5-9b` | 89.00 | 3 | 6 | 50.00% | 2/2 | 1/2 | 0/2 |
| `qwen3.5-35b-a3b` | 87.50 | 3 | 6 | 50.00% | 2/2 | 1/2 | 0/2 |
| `omnicoder-2-9b` | 62.00 | 2 | 6 | 33.33% | 2/2 | 0/2 | 0/2 |
| `omnicoder-9b-strand-rust-v1` | 47.00 | 2 | 6 | 33.33% | 1/2 | 1/2 | 0/2 |

## Notes

- `compile` contributes 30 points.
- `edition2024` contributes 30 points.
- `semantic` contributes 40 points.
- `fmt`-only and `clippy`-only failures keep discounted partial credit.
