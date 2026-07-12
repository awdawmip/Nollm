param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd")
$ErrorActionPreference = "Stop"
& $OpenClaw plugins uninstall nollm-formation --force
$agents = & $OpenClaw config get agents.list --json | ConvertFrom-Json
$mainIndex = [array]::IndexOf(@($agents.id), "main")
if ($mainIndex -ge 0) {
  $allow = @($agents[$mainIndex].tools.alsoAllow | Where-Object { $_ -ne "nollm_form_statement" })
  $batchFile = Join-Path $env:TEMP "nollm-formation-uninstall-$PID.json"
  try {
    $operations = [System.Collections.ArrayList]::new()
    [void]$operations.Add([ordered]@{ path="agents.list[$mainIndex].tools.alsoAllow"; value=$allow })
    ConvertTo-Json -InputObject $operations -Depth 5 | Set-Content $batchFile -Encoding utf8
    & $OpenClaw config set --batch-file $batchFile
  } finally { Remove-Item $batchFile -Force -ErrorAction SilentlyContinue }
}
