param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd")
$ErrorActionPreference = "Stop"
& $OpenClaw plugins uninstall nollm-formation --force
$dream = & $OpenClaw agents list --json | ConvertFrom-Json
if (@($dream.id) -contains "nollm-dream-agent") {
  & $OpenClaw agents delete nollm-dream-agent --force
}
$agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
$mainIndex = [array]::IndexOf(@($agents.id), "main")
$globalAllow = @(& $OpenClaw config get tools.alsoAllow --json | ConvertFrom-Json)
$globalAllow = @($globalAllow | Where-Object { $_ -notin @("nollm_form_statement", "nollm-formation") })
$operations = [System.Collections.ArrayList]::new()
[void]$operations.Add([ordered]@{ path="tools.alsoAllow"; value=$globalAllow })
if ($mainIndex -ge 0) {
  $allow = @($agents[$mainIndex].tools.alsoAllow | Where-Object { $_ -ne "nollm_form_statement" })
  [void]$operations.Add([ordered]@{ path="agents.list[$mainIndex].tools.alsoAllow"; value=$allow })
}
$batchFile = Join-Path $env:TEMP "nollm-formation-uninstall-$PID.json"
try {
  ConvertTo-Json -InputObject $operations -Depth 5 | Set-Content $batchFile -Encoding utf8
  & $OpenClaw config set --batch-file $batchFile
} finally { Remove-Item $batchFile -Force -ErrorAction SilentlyContinue }
