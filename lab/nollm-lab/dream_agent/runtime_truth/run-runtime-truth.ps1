param(
  [ValidateSet("enabled", "disabled")][string]$Mode,
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [string]$Profile = ""
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$output = Join-Path $PSScriptRoot $Mode
New-Item -ItemType Directory -Path $output -Force | Out-Null
$batch = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$prompts = @(
  "What makes a written explanation easy to follow?",
  "Give one practical reason to take short breaks while reading.",
  "How would you describe the color teal in one sentence?",
  "What is a simple way to compare two alternatives fairly?",
  "Name one benefit of writing down an important decision.",
  "Why can a short checklist be useful before a meeting?",
  "Give one example of a reversible everyday choice.",
  "What is the difference between a fact and an assumption?",
  "Why is the exact wording of an error useful when troubleshooting?",
  "Describe a calm morning routine in one sentence.",
  "What should a useful summary include?",
  "Why does chronological order help explain an event?",
  "What is an unresolved blocker?",
  "How can test results be summarized concisely?",
  "Why should a revised plan mention what changed?"
)
$receipts = [System.Collections.Generic.List[object]]::new()
for ($i = 0; $i -lt $prompts.Count; $i++) {
  $session = "aold-rev1-$Mode-$batch-s$([math]::Floor($i / 3) + 1)"
  $args = @()
  if ($Profile) { $args += @("--profile", $Profile) }
  $args += @("agent", "--agent", "main", "--session-id", $session, "--message", $prompts[$i], "--json", "--timeout", "180")
  $started = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $stdout = & $OpenClaw @args 2> (Join-Path $output ("turn-{0:d2}.stderr.txt" -f ($i + 1)))
  $exit = $LASTEXITCODE
  $returned = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $raw = ($stdout -join "`n")
  $raw | Set-Content (Join-Path $output ("turn-{0:d2}.json" -f ($i + 1))) -Encoding utf8NoBOM
  $visible = $null
  try {
    $parsed = $raw | ConvertFrom-Json
    $visible = $parsed.result.payloads | Where-Object { $_.text } | Select-Object -ExpandProperty text
  } catch {}
  [ordered]@{turn=$i+1;session_id=$session;exit_code=$exit;main_started_at=$started;main_command_returned_at=$returned;visible_assistant_messages=@($visible).Count} | ConvertTo-Json -Compress | Add-Content (Join-Path $output "receipts.jsonl") -Encoding utf8NoBOM
  if ($exit -ne 0) { throw "turn $($i+1) failed" }
}
[ordered]@{mode=$Mode;batch=$batch;sample_count=15;profile=$(if($Profile){$Profile}else{'user-active'});model='meituan/LongCat-2.0';provider='meituan';completed_at=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()} | ConvertTo-Json | Set-Content (Join-Path $output "run.json") -Encoding utf8NoBOM
