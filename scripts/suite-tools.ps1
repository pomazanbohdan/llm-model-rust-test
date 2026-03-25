function Resolve-CaseDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$CaseId
    )

    $Path = Join-Path $Root "cases"
    foreach ($Segment in ($CaseId -split '/')) {
        $Path = Join-Path $Path $Segment
    }
    return $Path
}

function Sanitize-CaseId {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CaseId
    )

    return ($CaseId -replace '[\\/]', '_')
}

function Reset-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [switch]$Force
    )

    if (Test-Path $Path) {
        if (-not $Force) {
            throw "Directory already exists: $Path"
        }
        Remove-Item $Path -Recurse -Force
    }

    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Copy-DirectoryContents {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null

    $Items = Get-ChildItem $Source -Force
    foreach ($Item in $Items) {
        $Target = Join-Path $Destination $Item.Name
        if ($Item.PSIsContainer) {
            Copy-DirectoryContents -Source $Item.FullName -Destination $Target
        }
        else {
            Copy-Item $Item.FullName $Target -Force
        }
    }
}

function Ensure-StandaloneCargoManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Directory
    )

    $ManifestPath = Join-Path $Directory "Cargo.toml"
    if (-not (Test-Path $ManifestPath)) {
        return
    }

    $Manifest = Get-Content $ManifestPath -Raw
    if ($Manifest -match '(^|\r?\n)\[workspace\](\r?\n|$)') {
        return
    }

    $Suffix = if ($Manifest.EndsWith("`n")) { "" } else { "`r`n" }
    Set-Content -Path $ManifestPath -Value ($Manifest + $Suffix + "`r`n[workspace]`r`n")
}

function Get-CaseMeta {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CaseDir
    )

    $MetaPath = Join-Path $CaseDir "meta.yaml"
    $Lines = Get-Content $MetaPath
    $Meta = @{
        id = ""
        title = ""
        layer = ""
        edition = ""
        checks = @()
    }

    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        $Line = $Lines[$Index]
        if ($Line -match '^id:\s*(.+?)\s*$') {
            $Meta.id = $Matches[1].Trim().Trim('"')
            continue
        }
        if ($Line -match '^title:\s*(.+?)\s*$') {
            $Meta.title = $Matches[1].Trim().Trim('"')
            continue
        }
        if ($Line -match '^layer:\s*(.+?)\s*$') {
            $Meta.layer = $Matches[1].Trim().Trim('"')
            continue
        }
        if ($Line -match '^edition:\s*(.+?)\s*$') {
            $Meta.edition = $Matches[1].Trim().Trim('"')
            continue
        }
        if ($Line -match '^checks:\s*$') {
            $Checks = New-Object System.Collections.Generic.List[string]
            for ($Inner = $Index + 1; $Inner -lt $Lines.Count; $Inner++) {
                $CheckLine = $Lines[$Inner]
                if ($CheckLine -match '^\s*-\s*(.+?)\s*$') {
                    $Checks.Add($Matches[1].Trim().Trim('"'))
                    continue
                }
                if ($CheckLine -match '^\S') {
                    break
                }
            }
            $Meta.checks = @($Checks)
        }
    }

    return [PSCustomObject]$Meta
}

function Get-DefaultChecksForLayer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Layer
    )

    switch ($Layer) {
        "compile" { return @("check", "clippy", "fmt", "doc") }
        "semantic" { return @("check", "clippy", "test", "fmt", "doc", "doctest") }
        "edition2024" { return @("check", "clippy", "test", "fmt", "doc", "doctest") }
        default { throw "No default checks configured for layer: $Layer" }
    }
}

function Get-ChecksForCase {
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Meta
    )

    if ($Meta.checks -and $Meta.checks.Count -gt 0) {
        return @($Meta.checks)
    }

    return @(Get-DefaultChecksForLayer -Layer $Meta.layer)
}

function Get-CommandSpec {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Check
    )

    switch ($Check) {
        "check" { return @{ program = "cargo"; args = @("check", "--all-targets") } }
        "clippy" { return @{ program = "cargo"; args = @("clippy", "--all-targets", "--", "-D", "warnings") } }
        "test" { return @{ program = "cargo"; args = @("test", "--all-targets") } }
        "fmt" { return @{ program = "cargo"; args = @("fmt", "--check") } }
        "doc" { return @{ program = "cargo"; args = @("doc", "--no-deps") } }
        "doctest" { return @{ program = "cargo"; args = @("test", "--doc") } }
        default { throw "Unknown check kind: $Check" }
    }
}

function Get-CaseList {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CasesRoot,
        [string]$RequestedCase,
        [string]$RequestedLayer
    )

    $MetaFiles = Get-ChildItem $CasesRoot -Recurse -Filter meta.yaml -File |
        Where-Object { $_.FullName -notmatch '\\cases\\_' }

    $Items = foreach ($MetaFile in $MetaFiles) {
        $CaseDir = Split-Path $MetaFile.FullName -Parent
        $Meta = Get-CaseMeta -CaseDir $CaseDir
        if (-not $Meta.id) {
            continue
        }

        [PSCustomObject]@{
            Id = $Meta.id
            Layer = $Meta.layer
        }
    }

    if ($RequestedCase) {
        $Items = $Items | Where-Object { $_.Id -eq $RequestedCase }
    }

    if ($RequestedLayer) {
        $Items = $Items | Where-Object { $_.Layer -eq $RequestedLayer }
    }

    return @($Items | Sort-Object Id)
}

function Prepare-CaseWorkspace {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [Parameter(Mandatory = $true)]
        [string]$CaseId,
        [Parameter(Mandatory = $true)]
        [string]$OutputDir,
        [switch]$Force
    )

    $CaseDir = Resolve-CaseDir -Root $RepoRoot -CaseId $CaseId
    if (-not (Test-Path $CaseDir)) {
        throw "Unknown case: $CaseId"
    }

    $StarterDir = Join-Path $CaseDir "starter"
    if (-not (Test-Path $StarterDir)) {
        throw "Missing starter directory for case: $CaseId"
    }

    Reset-Directory -Path $OutputDir -Force:$Force
    Copy-DirectoryContents -Source $StarterDir -Destination $OutputDir
    Ensure-StandaloneCargoManifest -Directory $OutputDir

    $EvalDir = Join-Path $OutputDir ".eval"
    New-Item -ItemType Directory -Path $EvalDir -Force | Out-Null
    Copy-Item (Join-Path $CaseDir "prompt.md") (Join-Path $EvalDir "prompt.md") -Force
    Copy-Item (Join-Path $CaseDir "meta.yaml") (Join-Path $EvalDir "meta.yaml") -Force
}

function Invoke-CaseEvaluation {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [Parameter(Mandatory = $true)]
        [string]$CaseId,
        [Parameter(Mandatory = $true)]
        [string]$SubmissionDir,
        [Parameter(Mandatory = $true)]
        [string]$ArtifactsDir
    )

    if (-not (Test-Path $SubmissionDir)) {
        throw "Submission directory does not exist: $SubmissionDir"
    }

    $CaseDir = Resolve-CaseDir -Root $RepoRoot -CaseId $CaseId
    $Meta = Get-CaseMeta -CaseDir $CaseDir
    $Checks = @(Get-ChecksForCase -Meta $Meta)

    Reset-Directory -Path $ArtifactsDir -Force
    Copy-DirectoryContents -Source $SubmissionDir -Destination $ArtifactsDir

    $OverlayDir = Join-Path (Join-Path $CaseDir "oracle") "overlay"
    if (Test-Path $OverlayDir) {
        Copy-DirectoryContents -Source $OverlayDir -Destination $ArtifactsDir
    }

    Ensure-StandaloneCargoManifest -Directory $ArtifactsDir

    $LogsDir = Join-Path $ArtifactsDir ".eval-logs"
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

    $Executions = New-Object System.Collections.Generic.List[object]
    $OverallSuccess = $true

    foreach ($Check in $Checks) {
        $Spec = Get-CommandSpec -Check $Check
        $StdoutLog = "$Check.stdout.log"
        $StderrLog = "$Check.stderr.log"
        $StdoutPath = Join-Path $LogsDir $StdoutLog
        $StderrPath = Join-Path $LogsDir $StderrLog

        $Start = Get-Date
        $Output = $null
        $ErrorText = $null
        $ExitCode = $null
        $Success = $false

        try {
            Push-Location $ArtifactsDir
            try {
                $Output = & $Spec.program @($Spec.args) 2>&1
                $ExitCode = $LASTEXITCODE
            }
            finally {
                Pop-Location
            }

            $Text = ($Output | Out-String)
            Set-Content -Path $StdoutPath -Value $Text
            Set-Content -Path $StderrPath -Value ""
            $Success = ($ExitCode -eq 0)
        }
        catch {
            $ErrorText = $_.Exception.Message
            Set-Content -Path $StdoutPath -Value ""
            Set-Content -Path $StderrPath -Value $ErrorText
            $Success = $false
        }

        if (-not $Success) {
            $OverallSuccess = $false
        }

        $DurationMs = [int][Math]::Round(((Get-Date) - $Start).TotalMilliseconds)
        $Executions.Add([PSCustomObject]@{
            check = $Check
            program = $Spec.program
            args = $Spec.args
            success = $Success
            exit_code = $ExitCode
            duration_ms = $DurationMs
            stdout_log = $StdoutLog
            stderr_log = $StderrLog
            error = $ErrorText
        })
    }

    $Report = [PSCustomObject]@{
        suite_version = 1
        case_id = $CaseId
        layer = $Meta.layer
        submission_dir = $SubmissionDir
        artifacts_dir = $ArtifactsDir
        success = $OverallSuccess
        checks = $Executions
    }

    $ReportPath = Join-Path $ArtifactsDir "report.json"
    $Report | ConvertTo-Json -Depth 6 | Set-Content -Path $ReportPath
    return $Report
}
