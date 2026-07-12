param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd")
$ErrorActionPreference = "Stop"
& $OpenClaw --version
$plugins = & $OpenClaw plugins list --json | ConvertFrom-Json
$plugin = $plugins.plugins | Where-Object id -eq "nollm-formation"
if (-not $plugin) { throw "nollm-formation is not registered" }
$inspect = & $OpenClaw plugins inspect nollm-formation --json | ConvertFrom-Json
$gateway = & $OpenClaw gateway status
$config = & $OpenClaw config get plugins.entries.nollm-formation --json | ConvertFrom-Json
$evidence = Join-Path $PSScriptRoot "..\..\..\..\docs\integration\openclaw\evidence\aold-natural-chat-live\live-cases.json"
[pscustomobject]@{
  id=$plugin.id; status=$plugin.status; source=$plugin.source; tools=$plugin.contracts.tools
  version=$inspect.version; prompt_version=$config.config.prompt_version
  schema_version=$config.config.schema_version; python_bridge=$config.config.python_executable
  gateway_status=($gateway -join "`n"); live_evidence=(Test-Path $evidence)
} | ConvertTo-Json -Depth 5
