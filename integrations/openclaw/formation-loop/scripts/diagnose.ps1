param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd")
$ErrorActionPreference = "Stop"
$plugins = & $OpenClaw plugins list --json | ConvertFrom-Json
$plugin = $plugins.plugins | Where-Object id -eq "nollm-formation"
if (-not $plugin) { throw "nollm-formation is not registered" }
$inspect = & $OpenClaw plugins inspect nollm-formation --json | ConvertFrom-Json
$config = & $OpenClaw config get plugins.entries.nollm-formation --json | ConvertFrom-Json
$agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
$dream = $agents | Where-Object id -eq "nollm-dream-agent"
[pscustomobject]@{
  id=$plugin.id; status=$plugin.status; version=$inspect.plugin.version; tools=@($inspect.plugin.toolNames)
  hooks=@("before_agent_run", "message_received", "llm_output", "message_sent", "agent_end"); model_mode=$config.config.model_mode
  dedicated_model=$config.config.model; write_mode=$config.config.write_mode
  persist_subagent_transcripts=$config.config.persist_subagent_transcripts
  python_bridge=$config.config.python_executable; dream_agent_present=($null -ne $dream)
  dream_agent_denies_message=(@($dream.tools.deny) -contains "message")
  dream_agent_allows_read=(@($dream.tools.allow) -contains "read")
  host_allow_model_override=$config.subagent.allowModelOverride
  host_allowed_models=@($config.subagent.allowedModels)
  plugin_allowed_models=@($config.config.allowed_models)
} | ConvertTo-Json -Depth 5
