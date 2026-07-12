param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd")
$ErrorActionPreference = "Stop"
& $OpenClaw --version
$plugins = & $OpenClaw plugins list --json | ConvertFrom-Json
$plugin = $plugins.plugins | Where-Object id -eq "nollm-formation"
if (-not $plugin) { throw "nollm-formation is not registered" }
$latest = Get-ChildItem (Join-Path $PSScriptRoot "..\..\..\..\lab\nollm-lab\openclaw_formation\runs") -Recurse -File -Filter *.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
[pscustomobject]@{ id=$plugin.id; status=$plugin.status; source=$plugin.source; tools=$plugin.contracts.tools; latest_run=$latest.FullName } | ConvertTo-Json -Depth 5
