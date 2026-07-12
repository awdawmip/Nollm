param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$env:PYTHONPATH = @("$repo\packages\nollm-core\src", "$repo\packages\nollm-access\src", "$repo\integrations\openclaw\formation-loop\python") -join ";"
$envelope = @{
  action = "parse_result"
  request = @{ request_id="smoke"; evidence=@(@{ evidence_id="e1"; content_utf8="Smoke evidence is exact."; source_handle="smoke.txt"; context_refs=@("smoke") }); max_statements=1 }
  openclaw_command = "openclaw.cmd"; model = "meituan/LongCat-2.0"
  prompt_version = "aold-v3"; schema_version = "aold-formation-v1"
  raw_model_response = '{"schema_version":"aold-formation-v1","outcome":"formed","selections":[{"evidence_id":"e1","start":0,"end":24,"statement_id":"smoke-s1"}],"reason_summary":"smoke"}'
  decision_id = "smoke-d1"
} | ConvertTo-Json -Depth 8 -Compress
$envelope | & $Python -m nollm_openclaw_formation.bridge
