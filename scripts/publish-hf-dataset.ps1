param(
    [Parameter(Mandatory = $true)]
    [string]$RepoId,
    [string]$LocalDir = "hf-dataset"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$ResolvedLocalDir = Join-Path $RepoRoot $LocalDir

if (-not (Test-Path $ResolvedLocalDir)) {
    throw "Local dataset directory not found: $ResolvedLocalDir"
}

$HfCommand = Get-Command hf -ErrorAction SilentlyContinue
if ($HfCommand) {
    & $HfCommand.Source upload $RepoId $ResolvedLocalDir . --repo-type dataset
    exit $LASTEXITCODE
}

$LegacyCommand = Get-Command huggingface-cli -ErrorAction SilentlyContinue
if ($LegacyCommand) {
    & $LegacyCommand.Source upload $RepoId $ResolvedLocalDir . --repo-type dataset
    exit $LASTEXITCODE
}

throw "Neither 'hf' nor 'huggingface-cli' is available in PATH. Install huggingface_hub CLI and login first."
