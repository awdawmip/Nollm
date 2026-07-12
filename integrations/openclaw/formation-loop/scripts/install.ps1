param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd", [string]$Model = "meituan/LongCat-2.0")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repo = (Resolve-Path (Join-Path $root "..\..\..")).Path
if (-not (Test-Path $OpenClaw)) { throw "OpenClaw not found: $OpenClaw" }
Push-Location $root
try { npm install --ignore-scripts; npm run build; & $OpenClaw plugins install --link $root } finally { Pop-Location }
$pythonExecutable = (& python -c "import sys; print(sys.executable)").Trim()
if (-not (Test-Path $pythonExecutable)) { throw "Python executable not found: $pythonExecutable" }
& $OpenClaw config set plugins.entries.nollm-formation.config.python_executable $pythonExecutable
& $OpenClaw config set plugins.entries.nollm-formation.config.nollm_repo_root $repo
& $OpenClaw config set plugins.entries.nollm-formation.config.openclaw_command $OpenClaw
& $OpenClaw config set plugins.entries.nollm-formation.config.model $Model
& $OpenClaw config set plugins.entries.nollm-formation.config.prompt_version aold-v3
& $OpenClaw config set plugins.entries.nollm-formation.config.schema_version aold-formation-v1
& $OpenClaw plugins enable nollm-formation
$agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
$mainIndex = [array]::IndexOf(@($agents.id), "main")
if ($mainIndex -lt 0) { throw "OpenClaw main agent is missing" }
$mainAllow = @($agents[$mainIndex].tools.alsoAllow)
if ($mainAllow -notcontains "nollm_form_statement") {
  & $OpenClaw config set "agents.list[$mainIndex].tools.alsoAllow[$($mainAllow.Count)]" nollm_form_statement
}
