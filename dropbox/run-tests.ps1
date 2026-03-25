$ErrorActionPreference = "Stop"

$DropRoot = $PSScriptRoot
$RepoRoot = Split-Path $DropRoot -Parent
$CaseFile = Join-Path $DropRoot "case-id.txt"
$WorkDir = Join-Path $DropRoot "work"
$ResultsDir = Join-Path $DropRoot "results"

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo is not available in PATH. Install Rust stable first."
}

if (-not (Test-Path $CaseFile)) {
    throw "Missing $CaseFile. Load a case first with .\scripts\load-dropbox.ps1 <case-id>."
}

if (-not (Test-Path $WorkDir)) {
    throw "Missing $WorkDir. Load a case first with .\scripts\load-dropbox.ps1 <case-id>."
}

$Case = (Get-Content $CaseFile -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($Case)) {
    throw "case-id.txt is empty."
}

Push-Location $RepoRoot
try {
    cargo run -p eval-suite -- run --case $Case --submission $WorkDir --artifacts $ResultsDir
    if ($LASTEXITCODE -ne 0) {
        throw "Evaluation failed for case: $Case"
    }
}
finally {
    Pop-Location
}

$Report = Join-Path $ResultsDir "report.json"

Write-Host ""
Write-Host "Finished evaluation:"
Write-Host "  case:    $Case"
Write-Host "  report:  $Report"
Write-Host "  logs:    $ResultsDir\.eval-logs"

