param(
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [ValidateSet("inherit", "dedicated")][string]$ModelMode = "inherit",
  [string]$Model = "",
  [ValidateSet("shadow-observation", "active-memory")][string]$Profile = "shadow-observation",
  [string]$StatementWorkspace = "",
  [string]$MemoryWorkspace = "",
  [string]$CaptureScope = "",
  [string]$PythonExecutable = ""
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repo = (Resolve-Path (Join-Path $root "..\..\..")).Path
if (-not (Test-Path $OpenClaw)) { throw "OpenClaw not found: $OpenClaw" }
if ($ModelMode -eq "dedicated" -and -not $Model) { throw "Dedicated mode requires -Model" }
$WriteMode = if ($Profile -eq "active-memory") { "statement-store" } else { "shadow" }
if ($Profile -eq "active-memory" -and -not $StatementWorkspace) { throw "active-memory profile requires -StatementWorkspace" }
if ($Profile -eq "active-memory" -and -not $CaptureScope) { throw "active-memory profile requires one explicit -CaptureScope" }
if (-not $CaptureScope) { $CaptureScope = "local-default-user" }
if ($Profile -eq "active-memory" -and -not $MemoryWorkspace) { $MemoryWorkspace = $StatementWorkspace }
Push-Location $root
try {
  npm install --ignore-scripts; if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
  npm run build; if ($LASTEXITCODE -ne 0) { throw "plugin build failed" }
  & $OpenClaw plugins install --link $root; if ($LASTEXITCODE -ne 0) { throw "OpenClaw plugin install failed" }
} finally { Pop-Location }
if (-not $PythonExecutable) {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) {
    $PythonExecutable = (& $pythonCommand.Source -c "import sys; print(sys.executable)").Trim()
  } else {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { $PythonExecutable = (& $launcher.Source -3 -c "import sys; print(sys.executable)").Trim() }
  }
}
if (-not $PythonExecutable -or -not (Test-Path -LiteralPath $PythonExecutable)) { throw "Python executable not found: $PythonExecutable" }
& $OpenClaw config set plugins.entries.nollm-formation.config.python_executable $PythonExecutable
& $OpenClaw config set plugins.entries.nollm-formation.config.nollm_repo_root $repo
& $OpenClaw config set plugins.entries.nollm-formation.config.enabled true
& $OpenClaw config set plugins.entries.nollm-formation.config.model_mode $ModelMode
& $OpenClaw config set plugins.entries.nollm-formation.config.write_mode $WriteMode
& $OpenClaw config set plugins.entries.nollm-formation.config.capture_scope_id $CaptureScope
& $OpenClaw config set plugins.entries.nollm-formation.config.memory_scope_mode single-configured-scope
& $OpenClaw config set plugins.entries.nollm-formation.config.absorption_directive_finalization_ms 30000
& $OpenClaw config set plugins.entries.nollm-formation.config.main_agent_operation_ttl_ms 300000
& $OpenClaw config set plugins.entries.nollm-formation.config.recall_atlas_max_regions 32
& $OpenClaw config set plugins.entries.nollm-formation.config.prompt_version dream-json-p1
& $OpenClaw config set plugins.entries.nollm-formation.config.persist_subagent_transcripts false
& $OpenClaw config set plugins.entries.nollm-formation.config.geometry_profile default_dream_v1
& $OpenClaw config set plugins.entries.nollm-formation.config.geometry_contract_version nollm_bounded_approximate_hex_coverage_v1
& $OpenClaw config set plugins.entries.nollm-formation.config.coordinate_domain_version nollm_hex_radius_2p31_default_chart_null_phase_v1
& $OpenClaw config set plugins.entries.nollm-formation.config.physical_residual_schema_version nollm_bounded_approximate_coverage_residual_v1
& $OpenClaw config set plugins.entries.nollm-formation.config.surface_wire_version nollm_openclaw_bounded_approximate_surface_traversal_v1
if ($Model) { & $OpenClaw config set plugins.entries.nollm-formation.config.model $Model }
if ($StatementWorkspace) { & $OpenClaw config set plugins.entries.nollm-formation.config.statement_store_workspace $StatementWorkspace }
if ($MemoryWorkspace) { & $OpenClaw config set plugins.entries.nollm-formation.config.memory_workspace $MemoryWorkspace }
& $OpenClaw plugins enable nollm-formation
& $OpenClaw config set plugins.entries.nollm-formation.hooks.allowConversationAccess true
& $OpenClaw config set plugins.entries.nollm-formation.subagent.allowModelOverride true
Write-Output "Nollm profile: $Profile"
Write-Output "Nollm write_mode: $WriteMode"
Write-Output "Nollm memory workspace: $MemoryWorkspace"
Write-Output "Nollm allowed capture scope: $CaptureScope"
Write-Output "Nollm memory scope mode: single-configured-scope"
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
  $allow = @($agents[$mainIndex].tools.alsoAllow | Where-Object { $_ -notin @("nollm_form_statement", "nollm_memory") }) + @("nollm_memory")
  [void]$operations.Add([ordered]@{ path="agents.list[$mainIndex].tools.alsoAllow"; value=$allow })
}
$batchFile = Join-Path $env:TEMP "nollm-dream-install-$PID.json"
try {
  ConvertTo-Json -InputObject $operations -Depth 6 | Set-Content $batchFile -Encoding utf8
  & $OpenClaw config set --batch-file $batchFile
} finally { Remove-Item $batchFile -Force -ErrorAction SilentlyContinue }
