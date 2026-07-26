param(
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [string]$OldWorkspace = ""
)
$ErrorActionPreference = "Stop"

$plugins = & $OpenClaw plugins list --json | ConvertFrom-Json
$plugin = $plugins.plugins | Where-Object id -eq "nollm-formation"
if (-not $plugin) { throw "nollm-formation is not registered" }
$inspect = & $OpenClaw plugins inspect nollm-formation --json | ConvertFrom-Json
$configEnvelope = & $OpenClaw config get plugins.entries.nollm-formation --json | ConvertFrom-Json
$config = $configEnvelope.config
$agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
$dream = $agents | Where-Object id -eq "nollm-dream-agent"
$main = $agents | Where-Object id -eq "main"
$captureRoot = if ($config.capture_workspace) {
  $config.capture_workspace
} elseif ($config.memory_workspace) {
  Join-Path $config.memory_workspace "openclaw-capture-spool"
} else {
  $null
}

$records = @()
$states = @()
if ($captureRoot -and (Test-Path -LiteralPath (Join-Path $captureRoot "captures"))) {
  $records = @(Get-ChildItem -LiteralPath (Join-Path $captureRoot "captures") -Filter "*.json" -File | ForEach-Object {
    try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
  } | Where-Object { $null -ne $_ })
  foreach ($record in $records) {
    $eventRoot = Join-Path (Join-Path $captureRoot "events") $record.capture_id
    $events = if (Test-Path -LiteralPath $eventRoot) {
      @(Get-ChildItem -LiteralPath $eventRoot -Filter "*.json" -File | ForEach-Object {
        try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
      } | Where-Object { $null -ne $_ })
    } else { @() }
    if ($events.Count -eq 0) {
      $states += [pscustomobject]@{ capture_id=$record.capture_id; status="captured"; event_epoch_ms=$record.captured_epoch_ms; attempt=0; batch_id=$null; error=$null }
    } else {
      $states += $events | Sort-Object -Property attempt,event_epoch_ms,@{Expression={ if ($_.status -eq "processing") { 1 } elseif ($_.status -eq "captured") { 0 } else { 2 } }},event_id | Select-Object -Last 1
    }
  }
}

$terminal = @("evaluated_no_new_propositions", "evaluated_no_new_propositions_legacy", "structural_invalid", "admitted", "reused", "revised")
$pending = @($states | Where-Object { $_.status -notin $terminal })
$now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$oldestPendingAgeMs = if ($pending.Count) { $now - (($pending | Measure-Object event_epoch_ms -Minimum).Minimum) } else { 0 }
$lastAdmitted = $states | Where-Object status -eq "admitted" | Sort-Object event_epoch_ms | Select-Object -Last 1
$lastError = $states | Where-Object { $_.error } | Sort-Object event_epoch_ms | Select-Object -Last 1
$latestCapture = $records | Sort-Object captured_epoch_ms | Select-Object -Last 1
$recentIntegrity = if ($null -eq $latestCapture) {
  "no_capture"
} else {
  $userBytes = [Text.Encoding]::UTF8.GetByteCount([string]$latestCapture.user_utf8)
  $assistantBytes = [Text.Encoding]::UTF8.GetByteCount([string]$latestCapture.assistant_utf8)
  if ($latestCapture.schema_version -eq "nollm_openclaw_durable_capture_v1" -and
      $latestCapture.user_role -eq "user" -and $latestCapture.assistant_role -eq "assistant" -and
      $userBytes -eq $latestCapture.user_utf8_bytes -and $assistantBytes -eq $latestCapture.assistant_utf8_bytes) { "valid" } else { "invalid" }
}

$oldWorkspacePresent = if ($OldWorkspace) {
  Test-Path -LiteralPath $OldWorkspace
} else {
  $memoryRoot = Join-Path $HOME ".openclaw\memory"
  [bool]((Test-Path -LiteralPath $memoryRoot) -and @(Get-ChildItem -LiteralPath $memoryRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.FullName -ne $config.memory_workspace }).Count)
}
$gatewayTask = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object TaskName -eq "OpenClaw Gateway" | Select-Object -First 1
$workerLockPresent = [bool]($captureRoot -and (Test-Path -LiteralPath (Join-Path $captureRoot "worker.lock")))
$toolEvidence = @()
$toolEvidenceCorrupt = @()
$toolRoot = if ($captureRoot) { Join-Path $captureRoot "tool-evidence" } else { $null }
if ($toolRoot -and (Test-Path -LiteralPath $toolRoot)) {
  foreach ($file in Get-ChildItem -LiteralPath $toolRoot -Filter "*.json" -File) {
    try {
      $item = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
      $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes([string]$item.tool_result_utf8))).ToLowerInvariant()
      if ($item.schema_version -ne "nollm_openclaw_tool_evidence_v1" -or $sha -ne $item.result_sha256) { throw "invalid Tool Evidence identity or result hash" }
      $toolEvidence += $item
    } catch { $toolEvidenceCorrupt += [pscustomobject]@{ file=$file.Name; error=[string]$_ } }
  }
}
$continuations = @($states | Where-Object status -eq "incomplete_continuation")
$uncoveredRangeCount = @($continuations | ForEach-Object { @($_.continuation.uncovered_ranges).Count } | Measure-Object -Sum).Sum
$retryStates = @($states | Where-Object { $_.status -in @("retryable_defer", "retryable_defer_legacy", "incomplete_continuation") })
$oldestRetryEpochMs = if ($retryStates.Count) { ($retryStates | Measure-Object event_epoch_ms -Minimum).Minimum } else { $null }

[pscustomobject]@{
  profile = if ($config.write_mode -eq "statement-store") { "active-memory" } else { "shadow-observation" }
  write_mode = $config.write_mode
  plugin_enabled = ($plugin.status -eq "loaded")
  plugin_version = $inspect.plugin.version
  capture_enabled = ($config.capture_enabled -ne $false)
  capture_workspace = $captureRoot
  capture_scope_id = $config.capture_scope_id
  memory_scope_mode = if ($config.memory_scope_mode) { $config.memory_scope_mode } else { "single-configured-scope" }
  absorption_directive_finalization_ms = if ($config.absorption_directive_finalization_ms) { $config.absorption_directive_finalization_ms } else { 30000 }
  memory_workspace = $config.memory_workspace
  statement_store_workspace = $config.statement_store_workspace
  worker_enabled = ($config.absorption_enabled -ne $false)
  worker_alive = [bool]($workerLockPresent -and $gatewayTask -and $gatewayTask.State -eq "Running")
  worker_lock_present = $workerLockPresent
  gateway_task_state = if ($gatewayTask) { [string]$gatewayTask.State } else { "missing" }
  pending_count = $pending.Count
  oldest_pending_age_ms = $oldestPendingAgeMs
  processing_batches = @($states | Where-Object status -eq "processing" | Select-Object -ExpandProperty batch_id -Unique)
  last_admitted_epoch_ms = $lastAdmitted.event_epoch_ms
  last_error = $lastError.error
  state_counts = [ordered]@{
    captured = @($states | Where-Object status -eq "captured").Count
    processing = @($states | Where-Object status -eq "processing").Count
    retryable_defer = @($states | Where-Object status -eq "retryable_defer").Count
    retryable_defer_legacy = @($states | Where-Object status -eq "retryable_defer_legacy").Count
    evaluated_no_new_propositions = @($states | Where-Object status -eq "evaluated_no_new_propositions").Count
    evaluated_no_new_propositions_legacy = @($states | Where-Object status -eq "evaluated_no_new_propositions_legacy").Count
    incomplete_continuation = $continuations.Count
    structural_invalid = @($states | Where-Object status -eq "structural_invalid").Count
    admitted = @($states | Where-Object status -eq "admitted").Count
    reused = @($states | Where-Object status -eq "reused").Count
    revised = @($states | Where-Object status -eq "revised").Count
  }
  retry_count = $retryStates.Count
  oldest_retry_epoch_ms = $oldestRetryEpochMs
  continuation_capture_count = $continuations.Count
  uncovered_source_range_count = if ($uncoveredRangeCount) { $uncoveredRangeCount } else { 0 }
  explicit_reevaluation_available = $true
  admitted_count = @($states | Where-Object status -eq "admitted").Count
  legacy_no_memory_count = @($states | Where-Object status -eq "no_memory").Count
  legacy_deferred_count = @($states | Where-Object status -eq "deferred").Count
  active_no_memory_terminal = $false
  active_deferred_terminal = $false
  tool_evidence_count = $toolEvidence.Count
  tool_evidence_corrupt_count = $toolEvidenceCorrupt.Count
  tool_evidence_corruption = $toolEvidenceCorrupt
  pending_fallback_enabled = ($config.pending_fallback_enabled -ne $false)
  pending_fallback_max_captures = if ($config.pending_fallback_max_captures) { $config.pending_fallback_max_captures } else { 4 }
  pending_fallback_max_chars = if ($config.pending_fallback_max_chars) { $config.pending_fallback_max_chars } else { 6000 }
  pending_fallback_max_age_ms = if ($config.pending_fallback_max_age_ms) { $config.pending_fallback_max_age_ms } else { 604800000 }
  recent_capture_integrity = $recentIntegrity
  old_workspace_present = $oldWorkspacePresent
  dream_agent_present = ($null -ne $dream)
  dream_agent_denies_message = (@($dream.tools.deny) -contains "message")
  main_agent_nollm_memory_allowed = (@($main.tools.alsoAllow) -contains "nollm_memory")
  main_agent_recall_enabled = ($config.main_agent_recall_enabled -ne $false)
  main_agent_operation_ttl_ms = if ($config.main_agent_operation_ttl_ms) { $config.main_agent_operation_ttl_ms } else { 300000 }
  recall_atlas_max_regions = if ($config.recall_atlas_max_regions) { $config.recall_atlas_max_regions } else { 32 }
  routing_surface_max_bytes = 8192
  routing_text_max_chars = 3000
  routing_anchor_max_chars = 131
  legacy_reader = $false
  legacy_formation_enabled = $false
  proposition_writer_schema_version = "nollm_openclaw_content_neutral_proposition_writer_v4"
  host_allow_model_override = $configEnvelope.subagent.allowModelOverride
  provider_model = if ($config.model) { $config.model } else { @($config.allowed_models) -join "," }
  active_evidence_path = $config.evidence_path
} | ConvertTo-Json -Depth 5
