param(
  [Parameter(Mandatory=$true)][ValidateRange(1,3)][int]$Round,
  [Parameter(Mandatory=$true)][ValidateSet("dream-v1","dream-v2")][string]$PromptVersion,
  [Parameter(Mandatory=$true)][ValidateSet("shadow","statement-store")][string]$WriteMode,
  [string]$StatementWorkspace = "",
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [ValidateRange(1,5)][int]$Concurrency = 5
)
$ErrorActionPreference = "Stop"
$runDir = Join-Path $PSScriptRoot "round-$Round"
$evidence = Join-Path $runDir "events.jsonl"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
Remove-Item -LiteralPath $evidence -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $runDir "turn-receipts.jsonl") -Force -ErrorAction SilentlyContinue
& $OpenClaw config set plugins.entries.nollm-formation.config.prompt_version $PromptVersion
& $OpenClaw config set plugins.entries.nollm-formation.config.write_mode $WriteMode
& $OpenClaw config set plugins.entries.nollm-formation.config.evidence_path $evidence
if ($WriteMode -eq "statement-store") {
  if (-not $StatementWorkspace) { throw "StatementWorkspace is required for round 3" }
  & $OpenClaw config set plugins.entries.nollm-formation.config.statement_store_workspace $StatementWorkspace
}
$restart = Start-Job -ArgumentList $OpenClaw -ScriptBlock { param($exe); & $exe gateway restart }
if (-not (Wait-Job $restart -Timeout 120)) { Stop-Job $restart }
Remove-Job $restart -Force
$deadline = (Get-Date).AddSeconds(60)
do {
  $listener = Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue
  if ($listener) { break }
  Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)
if (-not $listener) { throw "Gateway did not become ready on port 18789" }
Start-Sleep -Seconds 5

$messages = @(
  "I prefer weekly planning notes to begin with decisions and end with unresolved risks.",
  "For design reviews, I want constraints listed before alternatives.",
  "I reserve Tuesday mornings for architecture reviews.",
  "Please keep release notes concise and put breaking changes first.",
  "I organize research references by topic rather than by date.",
  "When a claim is uncertain, I want that uncertainty stated explicitly.",
  "I read incident reviews on Monday mornings and separate facts from hypotheses.",
  "For project meetings, I prefer written context before discussion.",
  "I keep deployment checklists ordered by user impact and rollback risk.",
  "My documentation style uses short headings and concrete examples.",
  "I avoid meetings after four in the afternoon whenever possible.",
  "For migration plans, I want compatibility risks before rollout steps.",
  "I archive design notes by month and list decisions before open questions.",
  "I prefer test reports that show failures before aggregate counts.",
  "For technical proposals, I want tradeoffs presented before recommendations."
)
$startedAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
for ($offset = 0; $offset -lt $messages.Count; $offset += $Concurrency) {
  $jobs = @()
  $end = [Math]::Min($offset + $Concurrency, $messages.Count)
  for ($index = $offset; $index -lt $end; $index++) {
    $turn = $index + 1
    $session = "aold-live-r$Round-t$('{0:d2}' -f $turn)"
    $output = Join-Path $runDir "turn-$('{0:d2}' -f $turn).json"
    $errorOutput = Join-Path $runDir "turn-$('{0:d2}' -f $turn).stderr.txt"
    $jobs += Start-Job -ArgumentList $OpenClaw,$session,$messages[$index],$output,$errorOutput -ScriptBlock {
      param($exe,$sessionId,$message,$out,$err)
      $started = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      & $exe agent --agent main --session-id $sessionId --message $message --json --timeout 240 1> $out 2> $err
      [pscustomobject]@{session_id=$sessionId; exit_code=$LASTEXITCODE; started_at=$started; returned_at=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()}
    }
  }
  $jobs | Wait-Job | Out-Null
  $jobs | Receive-Job | ForEach-Object {
    $_ | ConvertTo-Json -Depth 4 -Compress | Add-Content -LiteralPath (Join-Path $runDir "turn-receipts.jsonl") -Encoding utf8
  }
  $jobs | Remove-Job -Force
}
Start-Sleep -Seconds 150
$completedAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
[ordered]@{round=$Round; prompt_version=$PromptVersion; write_mode=$WriteMode; eligible_inputs=$messages.Count; started_at=$startedAt; completed_at=$completedAt; evidence_path=$evidence} |
  ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDir "round.json") -Encoding utf8
