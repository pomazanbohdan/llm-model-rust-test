param(
    [string]$Case,
    [string]$Layer,
    [int]$MaxCases = 0
)

$ErrorActionPreference = "Stop"

$ModelBox = $PSScriptRoot
$RepoRoot = Split-Path $ModelBox -Parent
$BenchmarkRoot = Join-Path $ModelBox "benchmark"
$RunsRoot = Join-Path $BenchmarkRoot "runs"
$SummaryJson = Join-Path $BenchmarkRoot "summary.json"
$SummaryCsv = Join-Path $BenchmarkRoot "summary.csv"
$Adapter = Join-Path $ModelBox "invoke-model.ps1"
$SuiteTools = Join-Path (Join-Path $RepoRoot "scripts") "suite-tools.ps1"
. $SuiteTools

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo is not available in PATH. Install Rust stable first."
}

if (-not (Test-Path $Adapter)) {
    throw "Missing model adapter: $Adapter"
}

function Sanitize-CaseId {
    param([string]$CaseId)
    return ($CaseId -replace '[\\/]', '_')
}

if (Test-Path $BenchmarkRoot) {
    Remove-Item $BenchmarkRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $RunsRoot -Force | Out-Null

$CaseIds = @((Get-CaseList -CasesRoot (Join-Path $RepoRoot "cases") -RequestedCase $Case -RequestedLayer $Layer) | Select-Object -ExpandProperty Id)

if ($MaxCases -gt 0) {
    $CaseIds = @($CaseIds | Select-Object -First $MaxCases)
}

if ($CaseIds.Count -eq 0) {
    throw "No cases matched the requested filters."
}

$Summary = New-Object System.Collections.Generic.List[object]

foreach ($CaseId in $CaseIds) {
    $CaseName = Sanitize-CaseId $CaseId
    $RunRoot = Join-Path $RunsRoot $CaseName
    $Workspace = Join-Path $RunRoot "workspace"
    $Results = Join-Path $RunRoot "results"
    $Prompt = Join-Path $RunRoot "prompt.md"
    $Meta = Join-Path $RunRoot "meta.yaml"
    $AdapterLog = Join-Path $RunRoot "model.log"

    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null

    Write-Host ""
    Write-Host "=== CASE: $CaseId ==="

    Prepare-CaseWorkspace -RepoRoot $RepoRoot -CaseId $CaseId -OutputDir $Workspace -Force

    $CaseDir = Resolve-CaseDir -Root $RepoRoot -CaseId $CaseId
    Copy-Item (Join-Path $CaseDir "prompt.md") $Prompt -Force
    Copy-Item (Join-Path $CaseDir "meta.yaml") $Meta -Force

    $InvokeStatus = "ok"
    $InvokeError = $null
    try {
        & $Adapter -PromptPath $Prompt -WorkspacePath $Workspace -MetaPath $Meta -LogPath $AdapterLog
    }
    catch {
        $InvokeStatus = "failed"
        $InvokeError = $_.Exception.Message
        if (-not (Test-Path $AdapterLog)) {
            $_ | Out-String | Set-Content -Path $AdapterLog
        }
    }

    if ($InvokeStatus -eq "failed") {
        $Summary.Add([PSCustomObject]@{
            case_id = $CaseId
            invoke_status = "failed"
            success = $false
            failed_checks = "invoke-model"
            report = ""
            note = $InvokeError
        })
        Write-Host "Model invocation failed: $InvokeError"
        continue
    }

    $null = Invoke-CaseEvaluation -RepoRoot $RepoRoot -CaseId $CaseId -SubmissionDir $Workspace -ArtifactsDir $Results

    $ReportPath = Join-Path $Results "report.json"
    if (-not (Test-Path $ReportPath)) {
        throw "Missing report.json for case: $CaseId"
    }

    $Report = Get-Content $ReportPath -Raw | ConvertFrom-Json
    $FailedChecks = @($Report.checks | Where-Object { -not $_.success } | ForEach-Object { $_.check }) -join ","

    $Summary.Add([PSCustomObject]@{
        case_id = $CaseId
        invoke_status = "ok"
        success = [bool]$Report.success
        failed_checks = $FailedChecks
        report = $ReportPath
        note = ""
    })

    Write-Host ("Result: success={0} failed_checks={1}" -f $Report.success, $FailedChecks)
}

$Totals = @{
    total = $Summary.Count
    passed = @($Summary | Where-Object { $_.success }).Count
    failed = @($Summary | Where-Object { -not $_.success }).Count
    invoke_failed = @($Summary | Where-Object { $_.invoke_status -ne "ok" }).Count
}

$Output = [PSCustomObject]@{
    generated_at = (Get-Date).ToString("s")
    filters = [PSCustomObject]@{
        case = $Case
        layer = $Layer
        max_cases = $MaxCases
    }
    totals = [PSCustomObject]$Totals
    cases = $Summary
}

$Output | ConvertTo-Json -Depth 6 | Set-Content -Path $SummaryJson
$Summary | Export-Csv -Path $SummaryCsv -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== SUMMARY ==="
Write-Host "total:         $($Totals.total)"
Write-Host "passed:        $($Totals.passed)"
Write-Host "failed:        $($Totals.failed)"
Write-Host "invoke_failed: $($Totals.invoke_failed)"
Write-Host "summary json:  $SummaryJson"
Write-Host "summary csv:   $SummaryCsv"
