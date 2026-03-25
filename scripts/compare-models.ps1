param(
    [Parameter(Mandatory = $true)]
    [string[]]$Models
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$WorkspacesRoot = Join-Path $RepoRoot "model-workspaces"
$ComparisonsRoot = Join-Path $WorkspacesRoot "comparisons"
$JsonPath = Join-Path $ComparisonsRoot "comparison.json"
$CsvPath = Join-Path $ComparisonsRoot "comparison.csv"

New-Item -ItemType Directory -Path $ComparisonsRoot -Force | Out-Null

$Rows = New-Object System.Collections.Generic.List[object]

foreach ($Model in $Models) {
    $SummaryPath = Join-Path (Join-Path $WorkspacesRoot $Model) "summary.json"
    if (-not (Test-Path $SummaryPath)) {
        throw "Missing summary for model '$Model': $SummaryPath"
    }

    $Summary = Get-Content $SummaryPath -Raw | ConvertFrom-Json
    $PassRate = if ($Summary.totals.total -gt 0) {
        [math]::Round(($Summary.totals.passed * 100.0) / $Summary.totals.total, 2)
    }
    else {
        0
    }

    $Rows.Add([PSCustomObject]@{
        model = $Summary.model
        model_id = $Summary.model_id
        total = $Summary.totals.total
        passed = $Summary.totals.passed
        failed = $Summary.totals.failed
        pass_rate = $PassRate
    })
}

$Output = [PSCustomObject]@{
    generated_at = (Get-Date).ToString("s")
    models = $Rows
}

$Output | ConvertTo-Json -Depth 5 | Set-Content -Path $JsonPath
$Rows | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== COMPARISON ==="
$Rows | Sort-Object pass_rate -Descending | Format-Table model, model_id, total, passed, failed, pass_rate
Write-Host "json: $JsonPath"
Write-Host "csv:  $CsvPath"
