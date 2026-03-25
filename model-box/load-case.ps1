param(
    [Parameter(Mandatory = $true)]
    [string]$Case
)

$ErrorActionPreference = "Stop"

$ModelBox = $PSScriptRoot
$RepoRoot = Split-Path $ModelBox -Parent
$WorkDir = Join-Path $ModelBox "workspace"
$ResultsDir = Join-Path $ModelBox "results"
$SuiteTools = Join-Path (Join-Path $RepoRoot "scripts") "suite-tools.ps1"
. $SuiteTools
$CaseDir = Resolve-CaseDir -Root $RepoRoot -CaseId $Case

if (-not (Test-Path $CaseDir)) {
    throw "Unknown case: $Case"
}

Prepare-CaseWorkspace -RepoRoot $RepoRoot -CaseId $Case -OutputDir $WorkDir -Force

if (Test-Path $ResultsDir) {
    Remove-Item $ResultsDir -Recurse -Force
}
New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null

Set-Content -Path (Join-Path $ModelBox "case-id.txt") -Value $Case -NoNewline
Copy-Item (Join-Path $CaseDir "prompt.md") (Join-Path $ModelBox "prompt.md") -Force
Copy-Item (Join-Path $CaseDir "meta.yaml") (Join-Path $ModelBox "meta.yaml") -Force

Write-Host ""
Write-Host "Model box is ready:"
Write-Host "  case:      $Case"
Write-Host "  prompt:    $ModelBox\prompt.md"
Write-Host "  workspace: $WorkDir"
Write-Host "  results:   $ResultsDir"
Write-Host ""
Write-Host "Next:"
Write-Host "  1. Give the model prompt.md and workspace\"
Write-Host "  2. Put the model output into workspace\"
Write-Host "  3. Run .\run-tests.ps1"
