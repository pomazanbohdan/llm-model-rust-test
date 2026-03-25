param(
    [Parameter(Mandatory = $true)]
    [string]$Case
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$DropRoot = Join-Path $RepoRoot "dropbox"
$WorkDir = Join-Path $DropRoot "work"
$ResultsDir = Join-Path $DropRoot "results"
$SuiteTools = Join-Path $PSScriptRoot "suite-tools.ps1"
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

Set-Content -Path (Join-Path $DropRoot "case-id.txt") -Value $Case -NoNewline
Copy-Item (Join-Path $CaseDir "prompt.md") (Join-Path $DropRoot "prompt.md") -Force
Copy-Item (Join-Path $CaseDir "meta.yaml") (Join-Path $DropRoot "meta.yaml") -Force

Write-Host ""
Write-Host "Loaded case into dropbox:"
Write-Host "  case:    $Case"
Write-Host "  prompt:  $DropRoot\prompt.md"
Write-Host "  work:    $WorkDir"
Write-Host "  results: $ResultsDir"
Write-Host ""
Write-Host "Next:"
Write-Host "  1. Put the model output into $WorkDir"
Write-Host "  2. Run .\dropbox\run-tests.ps1"
