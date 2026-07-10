$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
openclaw --version | Out-Null
node --version | Out-Null
openclaw plugins install --link $root
openclaw plugins enable nollm-grf
openclaw gateway restart
openclaw plugins inspect nollm-grf --runtime --json
