param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd", [string]$Model = "meituan/LongCat-2.0")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repo = (Resolve-Path (Join-Path $root "..\..\..")).Path
if (-not (Test-Path $OpenClaw)) { throw "OpenClaw not found: $OpenClaw" }
Push-Location $root
try { npm install --ignore-scripts; npm run build; & $OpenClaw plugins install --link $root } finally { Pop-Location }
& $OpenClaw config set plugins.entries.nollm-formation.config.python_executable (Get-Command python).Source
& $OpenClaw config set plugins.entries.nollm-formation.config.nollm_repo_root $repo
& $OpenClaw config set plugins.entries.nollm-formation.config.openclaw_command $OpenClaw
& $OpenClaw config set plugins.entries.nollm-formation.config.model $Model
& $OpenClaw plugins enable nollm-formation
