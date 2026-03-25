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
