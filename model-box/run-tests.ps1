$ErrorActionPreference = "Stop"

$ModelBox = $PSScriptRoot
$RepoRoot = Split-Path $ModelBox -Parent
$CaseFile = Join-Path $ModelBox "case-id.txt"
$WorkDir = Join-Path $ModelBox "workspace"
$ResultsDir = Join-Path $ModelBox "results"
$SuiteTools = Join-Path (Join-Path $RepoRoot "scripts") "suite-tools.ps1"
. $SuiteTools

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo is not available in PATH. Install Rust stable first."
}

if (-not (Test-Path $CaseFile)) {
    throw "Missing case-id.txt. Run .\load-case.ps1 <case-id> first."
}

if (-not (Test-Path $WorkDir)) {
    throw "Missing workspace\. Run .\load-case.ps1 <case-id> first."
}

$Case = (Get-Content $CaseFile -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($Case)) {
    throw "case-id.txt is empty."
}

$null = Invoke-CaseEvaluation -RepoRoot $RepoRoot -CaseId $Case -SubmissionDir $WorkDir -ArtifactsDir $ResultsDir

Write-Host ""
Write-Host "Finished evaluation:"
Write-Host "  case:    $Case"
Write-Host "  report:  $ResultsDir\report.json"
Write-Host "  logs:    $ResultsDir\.eval-logs"
