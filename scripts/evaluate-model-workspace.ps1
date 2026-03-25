param(
    [Parameter(Mandatory = $true)]
    [string]$Model
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$WorkspaceRoot = Join-Path (Join-Path $RepoRoot "model-workspaces") $Model
$ManifestPath = Join-Path $WorkspaceRoot "manifest.json"
$SummaryJson = Join-Path $WorkspaceRoot "summary.json"
$SummaryCsv = Join-Path $WorkspaceRoot "summary.csv"
. (Join-Path $PSScriptRoot "suite-tools.ps1")

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo is not available in PATH. Install Rust stable first."
}

if (-not (Test-Path $ManifestPath)) {
    throw "Missing model workspace manifest: $ManifestPath"
}

$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$Rows = New-Object System.Collections.Generic.List[object]

foreach ($Case in $Manifest.cases) {
    $CaseRoot = Join-Path $WorkspaceRoot $Case.folder
    $SubmissionRoot = Join-Path $CaseRoot "workspace"
    $ResultsRoot = Join-Path $CaseRoot "results"

    Write-Host ""
    Write-Host "=== EVAL: $($Case.case_id) ==="

    $Report = Invoke-CaseEvaluation -RepoRoot $RepoRoot -CaseId $Case.case_id -SubmissionDir $SubmissionRoot -ArtifactsDir $ResultsRoot

    $ReportPath = Join-Path $ResultsRoot "report.json"
    if (-not (Test-Path $ReportPath)) {
        throw "Missing report.json for case: $($Case.case_id)"
    }

    $Report = Get-Content $ReportPath -Raw | ConvertFrom-Json
    $FailedChecks = @($Report.checks | Where-Object { -not $_.success } | ForEach-Object { $_.check }) -join ","

    $Rows.Add([PSCustomObject]@{
        model = $Manifest.model
        model_id = $Manifest.model_id
        case_id = $Case.case_id
        layer = $Case.layer
        success = [bool]$Report.success
        failed_checks = $FailedChecks
        report = $ReportPath
    })
}

$LayerTotals = @{}
foreach ($Row in $Rows) {
    if (-not $LayerTotals.ContainsKey($Row.layer)) {
        $LayerTotals[$Row.layer] = @{
            total = 0
            passed = 0
            failed = 0
        }
    }

    $LayerTotals[$Row.layer].total += 1
    if ($Row.success) {
        $LayerTotals[$Row.layer].passed += 1
    }
    else {
        $LayerTotals[$Row.layer].failed += 1
    }
}

$Summary = [PSCustomObject]@{
    model = $Manifest.model
    model_id = $Manifest.model_id
    generated_at = (Get-Date).ToString("s")
    totals = [PSCustomObject]@{
        total = $Rows.Count
        passed = @($Rows | Where-Object { $_.success }).Count
        failed = @($Rows | Where-Object { -not $_.success }).Count
    }
    layers = $LayerTotals
    cases = $Rows
}

$Summary | ConvertTo-Json -Depth 6 | Set-Content -Path $SummaryJson
$Rows | Export-Csv -Path $SummaryCsv -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== MODEL SUMMARY ==="
Write-Host "model:   $($Manifest.model)"
Write-Host "total:   $($Summary.totals.total)"
Write-Host "passed:  $($Summary.totals.passed)"
Write-Host "failed:  $($Summary.totals.failed)"
Write-Host "summary: $SummaryJson"
