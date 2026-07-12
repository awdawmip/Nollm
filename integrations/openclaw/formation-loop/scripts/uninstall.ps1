param([string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd")
$ErrorActionPreference = "Stop"; & $OpenClaw plugins uninstall nollm-formation --force
