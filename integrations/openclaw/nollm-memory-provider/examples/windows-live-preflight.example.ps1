# Example: run Nollm P0-01 Windows OpenClaw live preflight
# This script is read-only: it does not modify config, restart the gateway,
# install/link plugins, or start Nollm Python sidecars.

$ErrorActionPreference = "Stop"

$OutputDirectory = "C:/Temp/nollm-preflight"
$OpenClawCommand = "openclaw"
$Profile = "default"

# Normalize output directory path to forward slashes for display.
$DisplayOutput = $OutputDirectory -replace "\\", "/"
Write-Host "Running Nollm P0-01 live preflight to: $DisplayOutput"

pwsh -NoProfile -ExecutionPolicy Bypass -File `
  "C:/Users/chaos/nollm/integrations/openclaw/nollm-memory-provider/tools/windows-live-preflight.ps1" `
  -OutputDirectory $OutputDirectory `
  -OpenClawCommand $OpenClawCommand `
  -Profile $Profile

Write-Host "Review the reports:"
Write-Host "  JSON: $DisplayOutput/WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.json"
Write-Host "  MD:   $DisplayOutput/WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.md"
