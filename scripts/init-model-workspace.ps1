param(
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [string]$Case,
    [string]$Layer,
    [int]$MaxCases = 0,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$WorkspacesRoot = Join-Path $RepoRoot "model-workspaces"
. (Join-Path $PSScriptRoot "suite-tools.ps1")

function Sanitize-Name {
    param([string]$Value)
    return ($Value -replace '[^A-Za-z0-9._-]', '_')
}

$ModelId = Sanitize-Name $Model
$WorkspaceRoot = Join-Path $WorkspacesRoot $ModelId
$CasesRoot = Join-Path $WorkspaceRoot "cases"
$ManifestPath = Join-Path $WorkspaceRoot "manifest.json"
$ReadmePath = Join-Path $WorkspaceRoot "README.md"
$GlobalPromptPath = Join-Path $WorkspaceRoot "GLOBAL_PROMPT.md"
$RunEvalPath = Join-Path $WorkspaceRoot "RUN_EVAL.ps1"
$ModelIdPath = Join-Path $WorkspaceRoot "MODEL_ID.txt"

if (Test-Path $WorkspaceRoot) {
    if (-not $Force) {
        throw "Workspace already exists: $WorkspaceRoot. Use -Force to recreate it."
    }
    Remove-Item $WorkspaceRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $CasesRoot -Force | Out-Null

$Cases = @(Get-CaseList -CasesRoot (Join-Path $RepoRoot "cases") -RequestedCase $Case -RequestedLayer $Layer)
if ($MaxCases -gt 0) {
    $Cases = @($Cases | Select-Object -First $MaxCases)
}

if ($Cases.Count -eq 0) {
    throw "No cases matched the requested filters."
}

$ManifestCases = New-Object System.Collections.Generic.List[object]

foreach ($Item in $Cases) {
    $CaseName = Sanitize-Name $Item.Id
    $CaseRoot = Join-Path $CasesRoot $CaseName
    $SubmissionRoot = Join-Path $CaseRoot "workspace"
    $ResultsRoot = Join-Path $CaseRoot "results"
    $SourceCaseDir = Resolve-CaseDir -Root $RepoRoot -CaseId $Item.Id

    New-Item -ItemType Directory -Path $CaseRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $ResultsRoot -Force | Out-Null

    Prepare-CaseWorkspace -RepoRoot $RepoRoot -CaseId $Item.Id -OutputDir $SubmissionRoot -Force

    Copy-Item (Join-Path $SourceCaseDir "prompt.md") (Join-Path $CaseRoot "prompt.md") -Force
    Copy-Item (Join-Path $SourceCaseDir "meta.yaml") (Join-Path $CaseRoot "meta.yaml") -Force
    Set-Content -Path (Join-Path $CaseRoot "case-id.txt") -Value $Item.Id -NoNewline

    $ManifestCases.Add([PSCustomObject]@{
        case_id = $Item.Id
        layer = $Item.Layer
        folder = ("cases/" + $CaseName)
    })
}

$Manifest = [PSCustomObject]@{
    model = $Model
    model_id = $ModelId
    generated_at = (Get-Date).ToString("s")
    filters = [PSCustomObject]@{
        case = $Case
        layer = $Layer
        max_cases = $MaxCases
    }
    cases = $ManifestCases
}

$Manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $ManifestPath
Set-Content -Path $ModelIdPath -Value $ModelId -NoNewline

$ReadmeLines = @(
    "# Model Workspace",
    "",
    "Model: $Model",
    "Folder id: $ModelId",
    "Model id file: MODEL_ID.txt",
    "",
    "This workspace contains one folder per benchmark case.",
    "",
    "For each case:",
    "",
    "1. open cases/<case>/prompt.md",
    "2. let the model edit only cases/<case>/workspace/",
    "3. keep the output in that workspace",
    "",
    "When all cases are ready, run:",
    "",
    ".\RUN_EVAL.ps1",
    ""
)

$ReadmeLines | Set-Content -Path $ReadmePath

$RunEvalLines = @(
    '$ErrorActionPreference = "Stop"',
    '$WorkspaceRoot = Split-Path $MyInvocation.MyCommand.Path -Parent',
    '$RepoRoot = Split-Path $WorkspaceRoot -Parent',
    '$ModelId = (Get-Content (Join-Path $WorkspaceRoot "MODEL_ID.txt") -Raw).Trim()',
    '& (Join-Path $RepoRoot "scripts\evaluate-model-workspace.ps1") -Model $ModelId'
)

$RunEvalLines | Set-Content -Path $RunEvalPath

$PromptLines = New-Object System.Collections.Generic.List[string]
$PromptLines.Add("# Rust Model Benchmark Prompt")
$PromptLines.Add("")
$PromptLines.Add("You are evaluating the model '$Model' on a multi-case Rust benchmark.")
$PromptLines.Add("")
$PromptLines.Add("Your task:")
$PromptLines.Add("1. Open manifest.json in the current workspace root.")
$PromptLines.Add("2. Iterate through every case listed there.")
$PromptLines.Add("3. For each case, read cases/<case-folder>/prompt.md and cases/<case-folder>/meta.yaml.")
$PromptLines.Add("4. Modify files only inside cases/<case-folder>/workspace/.")
$PromptLines.Add("5. Do not modify files in results/, manifest.json, or benchmark metadata.")
$PromptLines.Add("6. Preserve the public API requested by each case prompt.")
$PromptLines.Add("7. Target Rust edition 2024.")
$PromptLines.Add("8. Aim to pass all configured checks for every case: cargo check, cargo clippy -D warnings, cargo test, cargo fmt --check, cargo doc --no-deps, cargo test --doc when applicable.")
$PromptLines.Add("9. After you finish all cases, run this command from the current model workspace root:")
$PromptLines.Add("   .\RUN_EVAL.ps1")
$PromptLines.Add("10. If evaluation succeeds, keep all generated results under model-workspaces/$ModelId.")
$PromptLines.Add("")
$PromptLines.Add("Important constraints:")
$PromptLines.Add("- Work through all cases, not just one.")
$PromptLines.Add("- Do not stop after the first successful case.")
$PromptLines.Add("- Prefer minimal, correct, idiomatic Rust changes.")
$PromptLines.Add("- Hidden tests exist for semantic and edition-specific cases.")
$PromptLines.Add("")
$PromptLines.Add("Case folders in this workspace:")
foreach ($Entry in $ManifestCases) {
    $PromptLines.Add("- $($Entry.folder)")
}
$PromptLines.Add("")
$PromptLines.Add("Start by opening manifest.json, then process the cases one by one.")

$PromptLines | Set-Content -Path $GlobalPromptPath

Write-Host ""
Write-Host "Created model workspace:"
Write-Host "  model:     $Model"
Write-Host "  workspace: $WorkspaceRoot"
Write-Host "  cases:     $($ManifestCases.Count)"
Write-Host "  prompt:    $GlobalPromptPath"
Write-Host "  eval:      $RunEvalPath"
Write-Host ""
Write-Host "Next:"
Write-Host "  1. Give the model GLOBAL_PROMPT.md"
Write-Host "  2. Let it fill each case workspace and run .\RUN_EVAL.ps1"
