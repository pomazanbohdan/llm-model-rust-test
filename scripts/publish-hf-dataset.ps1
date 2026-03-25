param(
    [Parameter(Mandatory = $true)]
    [string]$RepoId,
    [string]$LocalDir = "hf-dataset",
    [string[]]$DeletePatterns = @()
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$ResolvedLocalDir = Join-Path $RepoRoot $LocalDir

if (-not (Test-Path $ResolvedLocalDir)) {
    throw "Local dataset directory not found: $ResolvedLocalDir"
}

$DeleteArgs = @()
foreach ($Pattern in $DeletePatterns) {
    $DeleteArgs += @("--delete", $Pattern)
}

$HfCommand = Get-Command hf -ErrorAction SilentlyContinue
if ($HfCommand) {
    & $HfCommand.Source upload $RepoId $ResolvedLocalDir . --repo-type dataset @DeleteArgs
    exit $LASTEXITCODE
}

$LegacyCommand = Get-Command huggingface-cli -ErrorAction SilentlyContinue
if ($LegacyCommand) {
    & $LegacyCommand.Source upload $RepoId $ResolvedLocalDir . --repo-type dataset @DeleteArgs
    exit $LASTEXITCODE
}

throw "Neither 'hf' nor 'huggingface-cli' is available in PATH. Install huggingface_hub CLI and login first."
