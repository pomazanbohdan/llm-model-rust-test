param(
    [Parameter(Mandatory = $true)]
    [string]$PromptPath,

    [Parameter(Mandatory = $true)]
    [string]$WorkspacePath,

    [Parameter(Mandatory = $true)]
    [string]$MetaPath,

    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

$ErrorActionPreference = "Stop"

@"
Model adapter is not configured.

Expected behavior:
- read the prompt from: $PromptPath
- optionally read metadata from: $MetaPath
- modify files only inside: $WorkspacePath
- write your own invocation log to: $LogPath

Edit model-box\invoke-model.ps1 and replace this placeholder with a call to your model.
"@ | Set-Content -Path $LogPath

throw "Model adapter is not configured. Edit model-box\invoke-model.ps1."

