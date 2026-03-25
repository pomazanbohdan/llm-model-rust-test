param(
    [string]$OutputDir = "hf-dataset",
    [string]$SourceDir = "personal-dataset\\train\\seed",
    [string]$DatasetVersion = "0.2.0",
    [string]$DatasetRepoId = "<your-username>/rustforge-personal-rust-dataset"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$ResolvedSource = Join-Path $RepoRoot $SourceDir
$ResolvedOutput = Join-Path $RepoRoot $OutputDir
$DataDir = Join-Path $ResolvedOutput "data"

if (-not (Test-Path $ResolvedSource)) {
    throw "Source directory not found: $ResolvedSource"
}

if (Test-Path $ResolvedOutput) {
    Remove-Item $ResolvedOutput -Recurse -Force
}

New-Item -ItemType Directory -Path $DataDir -Force | Out-Null

$ExampleFiles = Get-ChildItem $ResolvedSource -Filter *.json -File |
    Where-Object { $_.Name -ne "manifest.json" } |
    Sort-Object Name

if ($ExampleFiles.Count -eq 0) {
    throw "No example JSON files found in $ResolvedSource"
}

function Get-CodeFenceLanguage {
    param([string]$Path)

    $Extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    switch ($Extension) {
        ".rs" { return "rust" }
        ".toml" { return "toml" }
        ".md" { return "markdown" }
        ".yml" { return "yaml" }
        ".yaml" { return "yaml" }
        ".json" { return "json" }
        default { return "text" }
    }
}

function Join-TextLines {
    param([string[]]$Lines)
    return (($Lines | Where-Object { $_ -ne $null }) -join "`n").Trim()
}

function Format-WorkspaceFiles {
    param($Files)

    if (-not $Files) {
        return "No editable files were provided."
    }

    $Sections = @()
    foreach ($File in @($Files)) {
        $Fence = Get-CodeFenceLanguage -Path $File.path
        $Sections += Join-TextLines @(
            "File: $($File.path)",
            ('```' + $Fence),
            $File.content.TrimEnd("`r", "`n"),
            '```'
        )
    }

    return ($Sections -join "`n`n").Trim()
}

function Format-TargetFiles {
    param($Files)

    if (-not $Files) {
        return ""
    }

    $Blocks = @()
    foreach ($File in @($Files)) {
        $Blocks += Join-TextLines @(
            ('<file path="' + $File.path + '">'),
            $File.content.TrimEnd("`r", "`n"),
            "</file>"
        )
    }

    return ($Blocks -join "`n`n").Trim()
}

function Format-ConstraintBlock {
    param($Task)

    $Lines = @()
    foreach ($Constraint in @($Task.constraints)) {
        $Lines += "- $Constraint"
    }
    if ($Task.public_api_locked -eq $true) {
        $Lines += "- Keep the public API unchanged."
    }
    if ($Task.minimal_patch_expected -eq $true) {
        $Lines += "- Prefer the smallest correct patch."
    }
    if ($Lines.Count -eq 0) {
        $Lines += "- No additional constraints."
    }
    return ((@($Lines | Select-Object -Unique)) -join "`n")
}

function Build-SystemPrompt {
    return Join-TextLines @(
        "You are a Rust coding assistant.",
        "Solve the task using Rust edition 2024 semantics unless the prompt explicitly asks for a migration.",
        'Return only the final contents of the changed files using <file path="..."> blocks.'
    )
}

function Build-UserPrompt {
    param($Example)

    $WorkspaceText = Format-WorkspaceFiles -Files $Example.workspace.files
    $Constraints = Format-ConstraintBlock -Task $Example.task

    return Join-TextLines @(
        "Rust task id: $($Example.id)",
        "Category: $($Example.category)",
        "Difficulty: $($Example.difficulty)",
        "Edition target: $($Example.edition)",
        "",
        "Task:",
        $Example.task.instruction,
        "",
        "Constraints:",
        $Constraints,
        "",
        "Editable workspace files:",
        $WorkspaceText,
        "",
        "Response format:",
        '<file path="relative/path">',
        "...final file contents...",
        "</file>",
        "",
        "Return only the changed files."
    )
}

$Rows = foreach ($File in $ExampleFiles) {
    $Obj = Get-Content $File.FullName -Raw | ConvertFrom-Json
    $SystemPrompt = Build-SystemPrompt
    $UserPrompt = Build-UserPrompt -Example $Obj
    $AssistantCompletion = Format-TargetFiles -Files $Obj.target.files
    [PSCustomObject]@{
        dataset_version = $DatasetVersion
        split = "train"
        record_format = "chatml_messages"
        example_state = "draft_candidate"
        id = $Obj.id
        category = $Obj.category
        difficulty = $Obj.difficulty
        edition = $Obj.edition
        tier = $Obj.tier
        source_type = $Obj.source.type
        source_name = $Obj.source.name
        source_license_status = $Obj.source.license_status
        source_leakage_risk = $Obj.source.leakage_risk
        prompt = $UserPrompt
        completion = $AssistantCompletion
        system = $SystemPrompt
        messages = @(
            [PSCustomObject]@{
                role = "system"
                content = $SystemPrompt
            },
            [PSCustomObject]@{
                role = "user"
                content = $UserPrompt
            },
            [PSCustomObject]@{
                role = "assistant"
                content = $AssistantCompletion
            }
        )
        workspace_files = $Obj.workspace.files
        target_files = $Obj.target.files
        hidden_file_count = @($Obj.oracle.hidden_files).Count
        validation = $Obj.validation
        tags = $Obj.tags
    }
}

$JsonlPath = Join-Path $DataDir "train.jsonl"
foreach ($Row in $Rows) {
    ($Row | ConvertTo-Json -Depth 12 -Compress) | Add-Content -Path $JsonlPath
}

$Manifest = [PSCustomObject]@{
    dataset_name = "RustForge Personal Rust Dataset"
    dataset_version = $DatasetVersion
    generated_at = (Get-Date).ToString("s")
    source_dir = $SourceDir
    output_dir = $OutputDir
    dataset_repo_id = $DatasetRepoId
    train_rows = $Rows.Count
    record_format = "chatml_messages"
    unsloth_compatible = $true
    notes = "Unified Hugging Face export built from draft seed candidates in ChatML-compatible messages format."
}

$Manifest | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $ResolvedOutput "manifest.json")

$Readme = @'
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

Current version: `{{DATASET_VERSION}}`

Target Hub repo: `{{DATASET_REPO_ID}}`

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

ds = load_dataset("{{DATASET_REPO_ID}}", split="train")
print(ds[0]["messages"])
```

## Unsloth usage

```python
from datasets import load_dataset
from unsloth.chat_templates import get_chat_template

dataset = load_dataset("{{DATASET_REPO_ID}}", split="train")
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
'@ -replace '\{\{DATASET_VERSION\}\}', $DatasetVersion `
   -replace '\{\{DATASET_REPO_ID\}\}', $DatasetRepoId

$Readme | Set-Content -Path (Join-Path $ResolvedOutput "README.md")

Write-Host ""
Write-Host "Built unified dataset package:"
Write-Host "  output:    $ResolvedOutput"
Write-Host "  train rows: $($Rows.Count)"
Write-Host "  data file: $JsonlPath"
