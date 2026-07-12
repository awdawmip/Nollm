param(
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [ValidateSet("inherit", "dedicated")][string]$ModelMode = "inherit",
  [string]$Model = "",
  [ValidateSet("shadow", "statement-store")][string]$WriteMode = "shadow",
  [string]$StatementWorkspace = ""
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repo = (Resolve-Path (Join-Path $root "..\..\..")).Path
if (-not (Test-Path $OpenClaw)) { throw "OpenClaw not found: $OpenClaw" }
if ($ModelMode -eq "dedicated" -and -not $Model) { throw "Dedicated mode requires -Model" }
if ($WriteMode -eq "statement-store" -and -not $StatementWorkspace) { throw "statement-store mode requires -StatementWorkspace" }
Push-Location $root
try {
  npm install --ignore-scripts; if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
  npm run build; if ($LASTEXITCODE -ne 0) { throw "plugin build failed" }
  & $OpenClaw plugins install --link $root; if ($LASTEXITCODE -ne 0) { throw "OpenClaw plugin install failed" }
} finally { Pop-Location }
$pythonExecutable = (& python -c "import sys; print(sys.executable)").Trim()
if (-not (Test-Path $pythonExecutable)) { throw "Python executable not found: $pythonExecutable" }
& $OpenClaw config set plugins.entries.nollm-formation.config.python_executable $pythonExecutable
& $OpenClaw config set plugins.entries.nollm-formation.config.nollm_repo_root $repo
& $OpenClaw config set plugins.entries.nollm-formation.config.enabled true
& $OpenClaw config set plugins.entries.nollm-formation.config.model_mode $ModelMode
& $OpenClaw config set plugins.entries.nollm-formation.config.write_mode $WriteMode
& $OpenClaw config set plugins.entries.nollm-formation.config.prompt_version dream-v1
& $OpenClaw config set plugins.entries.nollm-formation.config.persist_subagent_transcripts false
if ($Model) { & $OpenClaw config set plugins.entries.nollm-formation.config.model $Model }
if ($StatementWorkspace) { & $OpenClaw config set plugins.entries.nollm-formation.config.statement_store_workspace $StatementWorkspace }
& $OpenClaw plugins enable nollm-formation
& $OpenClaw config set plugins.entries.nollm-formation.hooks.allowConversationAccess true
& $OpenClaw config set plugins.entries.nollm-formation.subagent.allowModelOverride true
$resolvedModel = if ($ModelMode -eq "dedicated") { $Model } else { & $OpenClaw config get agents.defaults.model.primary --json | ConvertFrom-Json }
if ($resolvedModel -isnot [string] -or -not $resolvedModel.Contains('/')) { throw "Host model must be a canonical provider/model reference" }
$hostAllowedModels = @($resolvedModel)
$hostAllowedModelsJson = ConvertTo-Json -InputObject $hostAllowedModels -Compress
& $OpenClaw config set plugins.entries.nollm-formation.subagent.allowedModels $hostAllowedModelsJson --strict-json
& $OpenClaw config set plugins.entries.nollm-formation.config.allowed_models $hostAllowedModelsJson --strict-json
$agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
if (@($agents.id) -notcontains "nollm-dream-agent") {
  $workspace = Join-Path $env:USERPROFILE ".openclaw\workspace-nollm-dream-agent"
  & $OpenClaw agents add nollm-dream-agent --non-interactive --workspace $workspace --json
  $agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
}
$dreamIndex = [array]::IndexOf(@($agents.id), "nollm-dream-agent")
$mainIndex = [array]::IndexOf(@($agents.id), "main")
$operations = [System.Collections.ArrayList]::new()
$globalAllow = @(& $OpenClaw config get tools.alsoAllow --json | ConvertFrom-Json)
$globalAllow = @($globalAllow | Where-Object { $_ -notin @("nollm_form_statement", "nollm-formation") })
[void]$operations.Add([ordered]@{ path="tools.alsoAllow"; value=$globalAllow })
[void]$operations.Add([ordered]@{ path="agents.list[$dreamIndex].tools.profile"; value="coding" })
[void]$operations.Add([ordered]@{ path="agents.list[$dreamIndex].tools.allow"; value=@("read") })
[void]$operations.Add([ordered]@{ path="agents.list[$dreamIndex].tools.alsoAllow"; value=@() })
[void]$operations.Add([ordered]@{ path="agents.list[$dreamIndex].tools.deny"; value=@("message", "sessions_spawn", "sessions_send", "sessions_yield") })
if ($mainIndex -ge 0) {
  $allow = @($agents[$mainIndex].tools.alsoAllow | Where-Object { $_ -ne "nollm_form_statement" })
  [void]$operations.Add([ordered]@{ path="agents.list[$mainIndex].tools.alsoAllow"; value=$allow })
}
$batchFile = Join-Path $env:TEMP "nollm-dream-install-$PID.json"
try {
  ConvertTo-Json -InputObject $operations -Depth 6 | Set-Content $batchFile -Encoding utf8
  & $OpenClaw config set --batch-file $batchFile
} finally { Remove-Item $batchFile -Force -ErrorAction SilentlyContinue }
