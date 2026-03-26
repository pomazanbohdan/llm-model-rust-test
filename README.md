# Rust Evaluation Suite

This repository contains a multi-layer Rust evaluation suite for LLM-assisted coding.
It is organized around independent layers so you can see where a model fails:

- compile correctness
- semantic correctness
- Rust 2024 compatibility
- async and concurrency
- unsafe and FFI
- macros
- API design and refactoring
- migration and repair

The initial scaffold in this repository focuses on Phase 1:

- `compile`
- `semantic`
- `edition2024`

The broader rollout and target benchmark size are documented in `docs/benchmark-plan.md`.

## Current Results

Composite score methodology for this leaderboard:

- `compile`: 30 points total
- `edition2024`: 30 points total
- `semantic`: 40 points total
- full pass gets full case credit
- `fmt`-only and `clippy`-only failures keep discounted partial credit

| Model | Score /100 | Passed | Total | Pass rate | Compile | Edition2024 | Semantic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `omnicoder-9b` | 92.00 | 4 | 6 | 66.67% | 2/2 | 2/2 | 0/2 |
| `qwen3.5-9b` | 89.00 | 3 | 6 | 50.00% | 2/2 | 1/2 | 0/2 |
| `qwen3.5-35b-a3b` | 87.50 | 3 | 6 | 50.00% | 2/2 | 1/2 | 0/2 |
| `omnicoder-2-9b` | 62.00 | 2 | 6 | 33.33% | 2/2 | 0/2 | 0/2 |
| `omnicoder-9b-strand-rust-v1` | 47.00 | 2 | 6 | 33.33% | 1/2 | 1/2 | 0/2 |

Detailed report:

- [reports/current-model-comparison.md](/C:/project/rust-test/reports/current-model-comparison.md)

## Personal Dataset

The repository now includes a separate personal Rust dataset scaffold under:

- [personal-dataset](/C:/project/rust-test/personal-dataset)

This is the starting point for a benchmark-aligned, execution-first Rust training dataset with:

- explicit acceptance rules
- a canonical example schema
- donor source policy
- a coverage matrix
- an implementation roadmap
- a first generated seed set of Rust task examples

It also includes a unified Hugging Face export pipeline:

- builder: [build-hf-unified-dataset.ps1](/C:/project/rust-test/scripts/build-hf-unified-dataset.ps1)
- publisher: [publish-hf-dataset.ps1](/C:/project/rust-test/scripts/publish-hf-dataset.ps1)
- output folder: [hf-dataset](/C:/project/rust-test/hf-dataset)
- published dataset: [pomazanbohdan/rustforge-personal-rust-dataset](https://huggingface.co/datasets/pomazanbohdan/rustforge-personal-rust-dataset)

The final export is designed as one unified SFT dataset:

- one unified `train` split stored as sharded `train-*.jsonl`
- ChatML-style `messages` rows for direct use in Unsloth
- `prompt` and `completion` convenience columns
- Rust task metadata and provenance kept in the same record

The current large HF-first build is now sharded as `train-*.jsonl` and generated from editable batch manifests under [hf-source](/C:/project/rust-test/hf-source).

Dataset pipeline:

```powershell
python .\scripts\strengthen-hf-dataset.py --max-per-category 10 --timeout-sec 90
python .\scripts\expand-hf-verified.py --window-size 10 --windows 10 --timeout-sec 90
python .\scripts\optimize-hf-train.py --target-rows 15000 --min-family-validated 20 --min-family-pass-rate 1.0 --aux-share 0.05
python .\scripts\parallel-improve-hf-dataset.py --validation-tier full --window-size 2 --waves 2 --start-offset 1 --workers 4 --timeout-sec 90 --target-rows 15000 --aux-share 0.05
```

Current dataset quality state:

- canonical corpus size: `56,000` rows
- current audited rows on the rebuilt corpus: `56,000`
- `0` failed audited rows
- all `13` dataset categories are now at `A+` by family depth
- global family-depth floor is now `1,000`
- current family-depth ceiling is `1,000`
- `56/56` families are now fully audited on the active corpus
- the active corpus is now uniformly audited at `A+` depth across every category

Current training subset:

- [hf-dataset-priority](/C:/project/rust-test/hf-dataset-priority)
- `14,998` rows
- `14,248` verified core rows
- `750` auxiliary rows

Current dataset reports:

- [reports/current-dataset-status.md](/C:/project/rust-test/reports/current-dataset-status.md)
- [reports/current-family-depth.md](/C:/project/rust-test/reports/current-family-depth.md)
- [reports/current-dataset-diversity.md](/C:/project/rust-test/reports/current-dataset-diversity.md)

## Layout

```text
cases/
  <layer>/
    <case-id>/
      meta.yaml
      prompt.md
      starter/
      oracle/
        overlay/
crates/
  eval-suite/
suite.toml
```

Each case contains:

- `prompt.md`: the exact task shown to the model
- `starter/`: the public workspace copied into a sandbox for the model
- `oracle/overlay/`: files merged only into the isolated evaluation run
- `meta.yaml`: tags, difficulty, layer, edition, flags

## Runner workflow

Recommended workflow for comparing multiple models:

```powershell
.\scripts\init-model-workspace.ps1 -Model qwen2.5-coder
.\scripts\evaluate-model-workspace.ps1 -Model qwen2.5-coder
.\scripts\compare-models.ps1 -Models qwen2.5-coder,deepseek-coder
```

This creates one isolated workspace per model under `model-workspaces/`, evaluates every prepared case, and writes a comparable summary for each model.

Each model workspace also contains a single top-level prompt file:

- `model-workspaces/<model>/GLOBAL_PROMPT.md`
- `model-workspaces/<model>/RUN_EVAL.ps1`

Give that one prompt to the model. It instructs the model to solve every case in the workspace and then run the local `RUN_EVAL.ps1` wrapper, so the model does not need to remember or retype the model id.

Single-case model workflow:

```powershell
cd .\model-box
.\load-case.ps1 semantic/parse-endpoint
.\run-tests.ps1
```

The model-facing folder is `model-box/` and contains the prompt, editable workspace, test results, and batch benchmark scripts.

Alternative workflow:

```powershell
.\scripts\load-dropbox.ps1 semantic/parse-endpoint
.\dropbox\run-tests.ps1
```

The active prompt, editable workspace, and test outputs all live under `dropbox/`.

Prepare a sandbox:

```powershell
cargo run -p eval-suite -- prepare --case semantic/parse-endpoint
```

This copies `starter/` into a sanitized directory under `.runs/prepared/` and attaches `.eval/prompt.md` plus `.eval/meta.yaml`.

Example default output path:

```text
.runs/prepared/semantic_parse-endpoint
```

Evaluate a submission:

```powershell
cargo run -p eval-suite -- run --case semantic/parse-endpoint --submission .runs/prepared/semantic_parse-endpoint
```

The runner will:

1. copy the submission into an isolated run directory
2. overlay hidden oracle files from `oracle/overlay/`
3. execute the configured Cargo checks for that layer
4. write logs and `report.json`

List and validate cases:

```powershell
cargo run -p eval-suite -- list
cargo run -p eval-suite -- validate
```

## Toolchain

The workspace targets Rust edition `2024` and expects a current stable toolchain with:

- `cargo`
- `rustc`
- `clippy`
- `rustfmt`

The provided `rust-toolchain.toml` pins the channel to `stable` and requests the required components.

## Extending the suite

Use `cases/_template/` as the template for new benchmarks.

Recommended metadata flags:

- `layer`
- `category`
- `difficulty`
- `repair_vs_generate`
- `requires_async`
- `unsafe`
- `ffi`
- `macro`
- `tags`

When you add `async`, `unsafe`, `macro`, or migration layers later, the same runner can reuse the existing case format and reporting pipeline.
