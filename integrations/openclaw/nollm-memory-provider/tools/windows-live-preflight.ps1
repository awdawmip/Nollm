# Nollm P0-01 Windows OpenClaw Live Preflight
# Read-only runtime fact collector. Does not modify config, restart gateway,
# install/link plugins, or run Nollm Python sidecars.
#
# Usage:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File windows-live-preflight.ps1 `
#     -OutputDirectory "C:/Temp/nollm-preflight" `
#     -OpenClawCommand "C:/path/to/openclaw.cmd"

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$OpenClawCommand,
    [string]$Profile = "default",
    [string]$ConfigPath,
    [string]$WorkspacePath,
    [string]$OpenClawStateDir,

    [switch]$NoProcessInspection,
    [switch]$JsonOnly
)

$ErrorActionPreference = "Stop"
$Script:CommandTimeoutMs = 15000
$Script:SchemaVersion = "nollm.windows_openclaw_preflight.v1"
$Script:Unknowns = [System.Collections.Generic.List[string]]::new()
$Script:Commands = [System.Collections.Generic.List[object]]::new()

# ---------------------------------------------------------------------------
# Platform gate
# ---------------------------------------------------------------------------
if (-not $IsWindows) {
    $payload = @{
        schema = $Script:SchemaVersion
        generated_at = (Get-Date -Format "o")
        platform = @{ os = "not_windows"; powershell_version = $PSVersionTable.PSVersion.ToString(); node = @{ status = "unavailable" } }
        safety = @{ mode = "read_only"; config_modified = $false; gateway_restarted = $false; plugin_installed_or_linked = $false; nollm_python_started = $false; legacy_memory_content_emitted = $false; transcript_content_emitted = $false }
        openclaw = @{ cli = @{}; profile = @{}; config = @{}; state = @{}; plugins = @{}; memory = @{}; sessions = @{} }
        workspace = @{ path = @{}; legacy_memory_metadata = @{}; bootstrap_risk = @{} }
        python = @{ interactive_shell = @{ candidates = @() }; gateway_environment = @{} }
        gateway_process = @{}
        readiness = @{ p1_node_only_probe = @{ status = "blocked"; blocking_reasons = @("platform_not_windows") }; p2_managed_python_probe = @{ status = "blocked"; blocking_reasons = @("platform_not_windows") } }
        operator_private_paths = @{
            output_directory = $OutputDirectory -replace "\\", "/"
        }
        unknowns = @("host platform is not Windows")
        commands = @()
    }
    $OutputDirectory = $OutputDirectory -replace "/", "\\"
    if (-not (Test-Path $OutputDirectory)) { New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null }
    $payload | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $OutputDirectory "WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.json") -Encoding utf8NoBOM
    exit 0
}

# ---------------------------------------------------------------------------
# Path normalization helpers
# ---------------------------------------------------------------------------
function ConvertTo-NollmPortablePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return @{ raw_input = ($Path -replace "\\", "/"); normalized_path = $null; exists = $false; resolution_status = "empty" }
    }
    if ($Path.StartsWith("\\")) {
        return @{ raw_input = ($Path -replace "\\", "/"); normalized_path = $null; exists = $false; resolution_status = "unsupported_unc" }
    }
    try {
        $resolved = (Resolve-Path -Path $Path -ErrorAction Stop).Path
        return @{ raw_input = ($Path -replace "\\", "/"); normalized_path = $resolved -replace "\\", "/"; exists = $true; resolution_status = "resolved" }
    } catch {
        return @{ raw_input = ($Path -replace "\\", "/"); normalized_path = $Path -replace "\\", "/"; exists = $false; resolution_status = "candidate_not_exists" }
    }
}

function Get-NollmPublicPath {
    param([string]$PortablePath)
    if ([string]::IsNullOrWhiteSpace($PortablePath)) { return $null }
    $homePortable = ($env:USERPROFILE -replace "\\", "/").TrimEnd("/")
    if ($PortablePath.StartsWith($homePortable + "/") -or $PortablePath -eq $homePortable) {
        return "%USERPROFILE%" + $PortablePath.Substring($homePortable.Length)
    }
    return $PortablePath
}

# ---------------------------------------------------------------------------
# Redaction helpers (no content is emitted, only structural secrets redacted)
# ---------------------------------------------------------------------------
$Script:SecretKeyPatterns = @("token", "secret", "password", "authorization", "api_key", "apikey", "cookie", "credential", "private_key")
$Script:SecretValuePatterns = @(
    [regex]::new("(Bearer\s+)\S+", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase),
    [regex]::new("\bsk-[a-zA-Z0-9]{20,}\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase),
    [regex]::new("\bghp_[a-zA-Z0-9]{30,}\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase),
    [regex]::new("\bgithub_pat_[a-zA-Z0-9]{22,}\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase),
    [regex]::new("\bxox[baprs]-[a-zA-Z0-9-]+\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase),
    [regex]::new("(api[_-]?key|apikey|token|password|secret|authorization)\s*[:=]\s*\S+", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
)

function Redact-StringValue {
    param([string]$Value)
    if ([string]::IsNullOrEmpty($Value)) { return $Value }
    $s = $Value
    foreach ($pat in $Script:SecretValuePatterns) {
        $s = $pat.Replace($s, {
            param($match)
            $prefix = ""
            if ($match.Groups.Count -gt 1 -and $match.Groups[1].Success) {
                $prefix = $match.Groups[1].Value
            }
            return $prefix + "<redacted>"
        })
    }
    return $s
}

function Redact-Value {
    param([object]$Value, [int]$Depth = 0)
    if ($Depth -gt 16) { return "<max-depth>" }
    if ($null -eq $Value) { return $Value }
    if ($Value -is [string]) { return Redact-StringValue -Value $Value }
    if ($Value -is [array]) { return @($Value | ForEach-Object { Redact-Value -Value $_ -Depth ($Depth + 1) }) }
    if ($Value -is [hashtable] -or $Value -is [System.Collections.Specialized.OrderedDictionary]) {
        $out = [ordered]@{}
        foreach ($k in $Value.Keys) {
            $isSecret = $Script:SecretKeyPatterns | Where-Object { $k.ToLowerInvariant().Contains($_) }
            $out[$k] = if ($isSecret) { "<redacted>" } else { Redact-Value -Value $Value[$k] -Depth ($Depth + 1) }
        }
        return $out
    }
    if ($Value -is [System.Management.Automation.PSCustomObject] -or ($Value.GetType().IsClass -and -not $Value.GetType().IsPrimitive)) {
        $out = [ordered]@{}
        $Value.PSObject.Properties | ForEach-Object {
            $isSecret = $Script:SecretKeyPatterns | Where-Object { $_.Name.ToLowerInvariant().Contains($_) }
            $out[$_.Name] = if ($isSecret) { "<redacted>" } else { Redact-Value -Value $_.Value -Depth ($Depth + 1) }
        }
        return $out
    }
    return $Value
}

# ---------------------------------------------------------------------------
# OpenClaw read-only invocation
# ---------------------------------------------------------------------------
function Invoke-NollmOpenClawReadOnly {
    param(
        [string]$CommandPath,
        [string[]]$ArgumentList,
        [string]$Source = "command"
    )
    $cmdName = Split-Path -Leaf $CommandPath
    $isPs1 = $CommandPath -match '\.ps1$'
    if ($isPs1) {
        # .ps1 wrappers need an interpreter; openclaw on Windows is commonly a ps1/cmd pair.
        $ArgumentList = @("-NoProfile", "-File", $CommandPath) + $ArgumentList
        $CommandPath = "pwsh"
        $cmdName = "pwsh"
    }
    $commandRecord = @{
        command = (($cmdName + " " + ($ArgumentList -join " ")) -replace "\\", "/")
        status = "unavailable"
        source = $Source
        exit_code = $null
        stdout_brief = $null
        stderr_brief = $null
    }
    if (-not (Test-Path $CommandPath) -and -not $isPs1) {
        $commandRecord.status = "unavailable"
        $Script:Commands.Add($commandRecord)
        return @{ status = "unavailable"; exit_code = $null; stdout = ""; stderr = ""; notes = @("command path not found") }
    }

    $outFile = [System.IO.Path]::GetTempFileName()
    $errFile = [System.IO.Path]::GetTempFileName()
    try {
        $proc = Start-Process -FilePath $CommandPath -ArgumentList $ArgumentList `
            -NoNewWindow -PassThru `
            -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        $waited = $proc.WaitForExit($Script:CommandTimeoutMs)
        if (-not $waited) {
            $proc.Kill($true)
            $commandRecord.status = "timeout"
            $Script:Commands.Add($commandRecord)
            return @{ status = "timeout"; exit_code = $null; stdout = ""; stderr = ""; notes = @("process did not exit within timeout") }
        }
        $stdout = ([System.IO.File]::ReadAllText($outFile) -replace "`r`n", "`n").TrimEnd("`n") -replace "\\", "/"
        $stderr = ([System.IO.File]::ReadAllText($errFile) -replace "`r`n", "`n").TrimEnd("`n") -replace "\\", "/"
        $stdout = Redact-StringValue -Value $stdout
        $stderr = Redact-StringValue -Value $stderr

        # Bound output length to avoid accidental transcript dumping.
        $max = 4096
        if ($stdout.Length -gt $max) { $stdout = $stdout.Substring(0, $max) + "<truncated>" }
        if ($stderr.Length -gt $max) { $stderr = $stderr.Substring(0, $max) + "<truncated>" }

        $commandRecord.status = "observed"
        $commandRecord.exit_code = $proc.ExitCode
        $commandRecord.stdout_brief = $stdout
        $commandRecord.stderr_brief = $stderr
        $Script:Commands.Add($commandRecord)
        return @{ status = "observed"; exit_code = $proc.ExitCode; stdout = $stdout; stderr = $stderr }
    } catch {
        $commandRecord.status = "blocked"
        $commandRecord.stderr_brief = (Redact-StringValue -Value $_.Exception.Message) -replace "\\", "/"
        $Script:Commands.Add($commandRecord)
        return @{ status = "blocked"; exit_code = $null; stdout = ""; stderr = (Redact-StringValue -Value $_.Exception.Message) -replace "\\", "/" }
    } finally {
        Remove-Item -Path $outFile -ErrorAction SilentlyContinue
        Remove-Item -Path $errFile -ErrorAction SilentlyContinue
    }
}

function Invoke-NollmOpenClawReadOnlyIfAvailable {
    param([string]$CommandPath, [string[]]$ArgumentList, [string]$Source = "command")
    if ([string]::IsNullOrWhiteSpace($CommandPath)) {
        return @{ status = "unavailable"; exit_code = $null; stdout = ""; stderr = ""; notes = @("command not resolved") }
    }
    return Invoke-NollmOpenClawReadOnly -CommandPath $CommandPath -ArgumentList $ArgumentList -Source $Source
}

# ---------------------------------------------------------------------------
# Resolve OpenClaw command
# ---------------------------------------------------------------------------
$resolvedOpenClaw = $null
if (-not [string]::IsNullOrWhiteSpace($OpenClawCommand)) {
    if (Test-Path $OpenClawCommand) {
        $resolvedOpenClaw = $OpenClawCommand
    } else {
        $found = Get-Command $OpenClawCommand -ErrorAction SilentlyContinue
        if ($found) { $resolvedOpenClaw = $found.Source }
    }
} else {
    $found = Get-Command "openclaw" -ErrorAction SilentlyContinue
    if ($found) {
        $resolvedOpenClaw = $found.Source
    }
}
if ($resolvedOpenClaw) {
    $resolvedOpenClaw = (ConvertTo-NollmPortablePath -Path $resolvedOpenClaw).normalized_path -replace "/", "\\"
}
$openClawInfo = @{
    status = if ($resolvedOpenClaw) { "observed" } else { "unavailable" }
    source = if ($resolvedOpenClaw) { "command" } else { "environment" }
    value = if ($resolvedOpenClaw) { ($resolvedOpenClaw -replace "\\", "/") } else { "openclaw command not found in PATH or argument" }
    notes = @()
}

# ---------------------------------------------------------------------------
# Environment / argument discovery
# ---------------------------------------------------------------------------
$userProfilePortable = ConvertTo-NollmPortablePath -Path $env:USERPROFILE
$stateDirPortable = if (-not [string]::IsNullOrWhiteSpace($OpenClawStateDir)) {
    ConvertTo-NollmPortablePath -Path $OpenClawStateDir
} elseif ($env:OPENCLAW_STATE_DIR) {
    ConvertTo-NollmPortablePath -Path $env:OPENCLAW_STATE_DIR
} else {
    ConvertTo-NollmPortablePath -Path (Join-Path $env:USERPROFILE ".openclaw")
}
$configPathPortable = if (-not [string]::IsNullOrWhiteSpace($ConfigPath)) {
    ConvertTo-NollmPortablePath -Path $ConfigPath
} elseif ($env:OPENCLAW_CONFIG_PATH) {
    ConvertTo-NollmPortablePath -Path $env:OPENCLAW_CONFIG_PATH
} else {
    ConvertTo-NollmPortablePath -Path (Join-Path $stateDirPortable.normalized_path "openclaw.json")
}
$workspacePathPortable = if (-not [string]::IsNullOrWhiteSpace($WorkspacePath)) {
    ConvertTo-NollmPortablePath -Path $WorkspacePath
} else {
    ConvertTo-NollmPortablePath -Path (Join-Path $env:USERPROFILE ".openclaw" "workspace")
}

# ---------------------------------------------------------------------------
# OpenClaw CLI identity
# ---------------------------------------------------------------------------
$versionResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("--version")
$helpResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("--help")
$pluginsHelpResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("plugins", "--help")
$configHelpResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("config", "--help")
$sessionsHelpResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("sessions", "--help")
$statusResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("status")
$pluginsListResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("plugins", "list")
$configValidateResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("config", "validate")
$gatewayStatusResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("gateway", "status")
$sessionsListResult = Invoke-NollmOpenClawReadOnlyIfAvailable -CommandPath $resolvedOpenClaw -ArgumentList @("sessions", "list")

$cliFacts = @{
    command_path = $openClawInfo
    version = @{ status = $versionResult.status; source = "command"; value = ($versionResult.stdout.Trim() -split "`r?`n")[0]; notes = @() }
    help_available = @{ status = $helpResult.status; source = "command"; value = ($helpResult.stdout.Length -gt 0); notes = @() }
    plugins_help_available = @{ status = $pluginsHelpResult.status; source = "command"; value = ($pluginsHelpResult.stdout.Length -gt 0); notes = @() }
    config_help_available = @{ status = $configHelpResult.status; source = "command"; value = ($configHelpResult.stdout.Length -gt 0); notes = @() }
    sessions_help_available = @{ status = $sessionsHelpResult.status; source = "command"; value = ($sessionsHelpResult.stdout.Length -gt 0); notes = @() }
    config_validate = @{ status = $configValidateResult.status; source = "command"; value = $configValidateResult.stdout.Trim(); notes = @() }
}
if ($cliFacts.version.value -and $cliFacts.version.value -match "OpenClaw\s+(\S+)") {
    $cliFacts.version.value = $Matches[1]
}

# ---------------------------------------------------------------------------
# Profile / config / state facts
# ---------------------------------------------------------------------------
$profileFacts = @{
    selected_profile = @{ status = "inferred"; source = "operator_argument"; value = $Profile; notes = @("default unless overridden") }
    interactive_shell_state_dir = @{ status = $stateDirPortable.resolution_status; source = "environment_or_argument"; value = $stateDirPortable.normalized_path; notes = @() }
    interactive_shell_config_path = @{ status = $configPathPortable.resolution_status; source = "environment_or_argument"; value = $configPathPortable.normalized_path; notes = @() }
    candidate_workspace_path = @{ status = $workspacePathPortable.resolution_status; source = "environment_or_argument"; value = $workspacePathPortable.normalized_path; notes = @() }
    gateway_environment_status = @{ status = "unavailable"; source = "process_metadata"; value = "not_observable_from_preflight"; notes = @("interactive shell environment is not gateway process environment") }
}

$configFacts = @{
    candidate_path = @{ status = $configPathPortable.resolution_status; source = "environment_or_argument"; value = $configPathPortable.normalized_path; notes = @() }
    exists = @{ status = "observed"; source = "filesystem_metadata"; value = (Test-Path $configPathPortable.normalized_path); notes = @() }
    validate_output = @{ status = $configValidateResult.status; source = "command"; value = $configValidateResult.stdout.Trim(); notes = @() }
}

$stateFacts = @{
    candidate_path = @{ status = $stateDirPortable.resolution_status; source = "environment_or_argument"; value = $stateDirPortable.normalized_path; notes = @() }
    exists = @{ status = "observed"; source = "filesystem_metadata"; value = (Test-Path $stateDirPortable.normalized_path); notes = @() }
}

# ---------------------------------------------------------------------------
# Memory owner / plugin facts
# ---------------------------------------------------------------------------
$pluginFacts = @{
    plugins_help_available = @{ status = $pluginsHelpResult.status; source = "command"; value = ($pluginsHelpResult.stdout.Length -gt 0); notes = @() }
    plugins_list_available = @{ status = $pluginsListResult.status; source = "command"; value = ($pluginsListResult.stdout.Length -gt 0); notes = @() }
    list_output_brief = @{ status = $pluginsListResult.status; source = "command"; value = $pluginsListResult.stdout.Trim(); notes = @() }
    discovery_mechanism = @{ status = "inferred"; source = "command"; value = "inspect_plugins_help_and_list"; notes = @("P1 should use CLI link or workspace load path after confirming version") }
}

$memorySlot = "unknown_from_cli"
$memoryOwner = "unknown_from_cli"
if ($configValidateResult.stdout -match 'memory') {
    $memorySlot = "memory_slot_mentioned_in_config_validate"
}
if ($pluginsListResult.stdout -match "nollm") {
    $memoryOwner = "nollm_plugin_present_in_list"
}
$companionListed = $pluginsListResult.stdout -match "nollm-memory-companion"
$providerListed = $pluginsListResult.stdout -match "nollm-memory-provider"
$companionState = if ($companionListed) { "observed" } else { "unavailable" }
$companionValue = if ($companionListed) { "listed" } else { "unknown_from_cli" }
$providerState = if ($providerListed) { "observed" } else { "unavailable" }
$providerValue = if ($providerListed) { "listed" } else { "unknown_from_cli" }
$memoryFacts = @{
    plugins_slots_memory = @{ status = "unavailable"; source = "command"; value = $memorySlot; notes = @("not read from config file directly") }
    selected_memory_provider = @{ status = $(if ($memoryOwner -ne "unknown_from_cli") { "observed" } else { "unavailable" }); source = "command"; value = $memoryOwner; notes = @() }
    memory_core_state = @{ status = "unavailable"; source = "command"; value = "unknown_from_cli"; notes = @() }
    active_memory_state = @{ status = "unavailable"; source = "command"; value = "unknown_from_cli"; notes = @() }
    nollm_memory_companion_state = @{ status = $companionState; source = "command"; value = $companionValue; notes = @() }
    nollm_provider_state = @{ status = $providerState; source = "command"; value = $providerValue; notes = @() }
}

# ---------------------------------------------------------------------------
# Session / transcript facts (metadata only)
# ---------------------------------------------------------------------------
$sessionIndexPath = Join-Path $stateDirPortable.normalized_path "sessions"
$transcriptRootPath = Join-Path $stateDirPortable.normalized_path "sessions"
$sessionsFacts = @{
    sessions_help_available = @{ status = $sessionsHelpResult.status; source = "command"; value = ($sessionsHelpResult.stdout.Length -gt 0); notes = @() }
    list_output_brief = @{ status = $sessionsListResult.status; source = "command"; value = $sessionsListResult.stdout.Trim(); notes = @() }
    session_index_path = @{ status = if (Test-Path $sessionIndexPath) { "observed" } else { "unavailable" }; source = "filesystem_metadata"; value = (ConvertTo-NollmPortablePath -Path $sessionIndexPath).normalized_path; notes = @() }
    transcript_root_path = @{ status = if (Test-Path $transcriptRootPath) { "observed" } else { "unavailable" }; source = "filesystem_metadata"; value = (ConvertTo-NollmPortablePath -Path $transcriptRootPath).normalized_path; notes = @() }
    transcript_store_status = @{ status = "observed"; source = "inference"; value = "metadata_only"; notes = @("content is not collected") }
    current_session_id = @{ status = "unavailable"; source = "command"; value = "not_redacted"; notes = @("P1 may query session index metadata") }
    file_count = @{ status = "unavailable"; source = "command"; value = $null; notes = @() }
    total_byte_size = @{ status = "unavailable"; source = "command"; value = $null; notes = @() }
    last_modified_time = @{ status = "unavailable"; source = "command"; value = $null; notes = @() }
}

# ---------------------------------------------------------------------------
# Legacy workspace memory metadata (no content read)
# ---------------------------------------------------------------------------
function Get-NollmFileMetadata {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return @{ exists = $false; size_bytes = $null; last_modified = $null; content_hash_computed = $false; content_not_emitted = $true }
    }
    $item = Get-Item -Path $Path -ErrorAction SilentlyContinue
    return @{
        exists = $true
        size_bytes = $item.Length
        last_modified = $item.LastWriteTimeUtc.ToString("o")
        content_hash_computed = $false
        content_not_emitted = $true
    }
}

function Get-NollmDirectoryMetadata {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return @{ exists = $false; file_count = $null; total_byte_size = $null; newest_mtime = $null; content_not_emitted = $true }
    }
    $items = Get-ChildItem -Path $Path -File -ErrorAction SilentlyContinue
    $total = ($items | Measure-Object -Property Length -Sum).Sum
    $newest = ($items | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
    return @{
        exists = $true
        file_count = $items.Count
        total_byte_size = [long]$total
        newest_mtime = if ($newest) { $newest.ToString("o") } else { $null }
        content_not_emitted = $true
    }
}

$memoryMdPath = Join-Path $workspacePathPortable.normalized_path "MEMORY.md"
$dreamsMdPath = Join-Path $workspacePathPortable.normalized_path "DREAMS.md"
$memoryDirPath = Join-Path $workspacePathPortable.normalized_path "memory"

$legacyMetadata = @{
    MEMORY_md = Get-NollmFileMetadata -Path $memoryMdPath
    DREAMS_md = Get-NollmFileMetadata -Path $dreamsMdPath
    memory_directory = Get-NollmDirectoryMetadata -Path $memoryDirPath
    note = "hashes are optional in P0; content is never read"
}

# ---------------------------------------------------------------------------
# Workspace bootstrap risk
# ---------------------------------------------------------------------------
$bootstrapRisk = "unavailable"
if ($legacyMetadata.MEMORY_md.exists -or $legacyMetadata.memory_directory.exists) {
    $bootstrapRisk = "likely_from_version_and_workspace_layout"
}
$bootstrapFacts = @{
    risk_level = @{ status = if ($bootstrapRisk -eq "unavailable") { "unavailable" } else { "inferred" }; source = "filesystem_metadata"; value = $bootstrapRisk; notes = @("based on presence of MEMORY.md / memory/; actual prompt injection requires P1 Node-only probe") }
    workspace_files_present = @{ status = "observed"; source = "filesystem_metadata"; value = @($memoryMdPath, $dreamsMdPath, $memoryDirPath | ForEach-Object { (Test-Path $_) }); notes = @() }
}

# ---------------------------------------------------------------------------
# Python interpreter visibility
# ---------------------------------------------------------------------------
$pythonCandidates = [System.Collections.Generic.List[object]]::new()
foreach ($pyName in @("py", "python", "python3")) {
    $found = Get-Command $pyName -ErrorAction SilentlyContinue
    if (-not $found) { continue }
    $where = (where.exe $pyName 2>$null) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    $probe = @{ status = "unavailable"; executable = $null; version = $null; notes = @() }
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $found.Source
        $psi.Arguments = '-c "import json,sys; print(json.dumps({\"executable\":sys.executable,\"version\":sys.version}))"'
        $psi.RedirectStandardOutput = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        $waited = $p.WaitForExit($Script:CommandTimeoutMs)
        if (-not $waited) { $p.Kill($true) }
        $raw = ($p.StandardOutput.ReadToEnd() -replace "`r`n", "`n").Trim()
        if ($raw) {
            $parsed = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue
            $probe.status = "observed"
            $probe.executable = $parsed.executable -replace "\\", "/"
            $probe.version = $parsed.version
        }
    } catch {
        $probe.status = "blocked"
        $probe.notes = @($_.Exception.Message)
    }
    $pythonCandidates.Add(@{
        name = $pyName
        resolved_path = ($found.Source -replace "\\", "/")
        where_entries = @($where | ForEach-Object { $_ -replace "\\", "/" })
        probe = $probe
    })
}

$pythonFacts = @{
    interactive_shell = @{ candidates = $pythonCandidates }
    gateway_environment = @{ status = "unavailable"; source = "process_metadata"; value = "not_observable_without_gateway_probe"; notes = @("do not substitute interactive shell PATH for gateway PATH") }
}

# ---------------------------------------------------------------------------
# Gateway process metadata
# ---------------------------------------------------------------------------
$gatewayProcessFacts = @{
    inspection_enabled = (-not $NoProcessInspection)
    status = "unavailable"
    processes = @()
    notes = @()
}
if (-not $NoProcessInspection) {
    try {
        $processes = Get-CimInstance Win32_Process | Where-Object {
            $_.Name -in @("node.exe", "openclaw.exe") -or $_.Name -like "*gateway*"
        }
        $gatewayProcessFacts.status = "observed"
        $gatewayProcessFacts.processes = @($processes | ForEach-Object {
            $cmdLine = (Redact-StringValue -Value $_.CommandLine) -replace "\\", "/"
            if ($cmdLine.Length -gt 512) { $cmdLine = $cmdLine.Substring(0, 512) + "<truncated>" }
            @{
                pid = $_.ProcessId
                name = $_.Name
                executable_path = ($_.ExecutablePath -replace "\\", "/")
                command_line_summary = $cmdLine
                owner_query_success = $false
                start_time = if ($_.CreationDate) { [System.Management.Automation.ManagementDateTimeConverter]::ToDateTime($_.CreationDate).ToString("o") } else { $null }
            }
        })
    } catch {
        $gatewayProcessFacts.status = "blocked"
        $gatewayProcessFacts.notes = @($_.Exception.Message)
    }
} else {
    $gatewayProcessFacts.notes = @("operator disabled process inspection")
}

# ---------------------------------------------------------------------------
# Readiness gates
# ---------------------------------------------------------------------------
$p1Blocking = [System.Collections.Generic.List[string]]::new()
if (-not $resolvedOpenClaw) { $p1Blocking.Add("openclaw_command_not_resolved") }
if ($versionResult.status -ne "observed") { $p1Blocking.Add("openclaw_version_not_observed") }
if (-not $configPathPortable.normalized_path) { $p1Blocking.Add("config_path_not_observed") }
if ($pluginsHelpResult.status -ne "observed" -and $pluginsListResult.status -ne "observed") { $p1Blocking.Add("plugin_commands_not_identified") }
if ($memoryFacts.selected_memory_provider.value -eq "unknown_from_cli") { $p1Blocking.Add("memory_owner_not_observed") }

$p1Ready = if ($p1Blocking.Count -eq 0) { "ready" } else { "blocked" }

$p2Blocking = [System.Collections.Generic.List[string]]::new()
if ($p1Ready -ne "ready") { $p2Blocking.Add("p1_not_ready") }
$usablePython = $pythonCandidates | Where-Object { $_.probe.status -eq "observed" -and $_.probe.executable }
if (-not $usablePython) { $p2Blocking.Add("no_absolute_python_candidate") }
$p2Ready = if ($p2Blocking.Count -eq 0) { "ready" } else { "blocked" }

$readinessFacts = @{
    p1_node_only_probe = @{ status = $p1Ready; blocking_reasons = @($p1Blocking) }
    p2_managed_python_probe = @{ status = $p2Ready; blocking_reasons = @($p2Blocking) }
}

# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------
$nodeVersion = (& { try { (& node --version 2>$null) } catch { $null } })
$report = [ordered]@{
    schema = $Script:SchemaVersion
    generated_at = (Get-Date -Format "o")
    platform = [ordered]@{
        os = "Windows"
        powershell_version = $PSVersionTable.PSVersion.ToString()
        node = [ordered]@{
            status = if ($nodeVersion) { "observed" } else { "unavailable" }
            value = ($nodeVersion -split "`r?`n")[0]
            notes = @()
        }
    }
    safety = [ordered]@{
        mode = "read_only"
        config_modified = $false
        gateway_restarted = $false
        plugin_installed_or_linked = $false
        nollm_python_started = $false
        legacy_memory_content_emitted = $false
        transcript_content_emitted = $false
    }
    openclaw = [ordered]@{
        cli = $cliFacts
        profile = $profileFacts
        config = $configFacts
        state = $stateFacts
        plugins = $pluginFacts
        memory = $memoryFacts
        sessions = $sessionsFacts
    }
    workspace = [ordered]@{
        path = @{ candidate_path = $workspacePathPortable }
        legacy_memory_metadata = $legacyMetadata
        bootstrap_risk = $bootstrapFacts
    }
    python = $pythonFacts
    gateway_process = $gatewayProcessFacts
    readiness = $readinessFacts
    operator_private_paths = [ordered]@{
        openclaw_command = ($resolvedOpenClaw -replace "\\", "/")
        output_directory = ($OutputDirectory -replace "\\", "/")
        state_dir = $stateDirPortable.normalized_path
        config_path = $configPathPortable.normalized_path
        workspace_path = $workspacePathPortable.normalized_path
    }
    unknowns = @($Script:Unknowns)
    commands = @($Script:Commands)
}

# ---------------------------------------------------------------------------
# Emit JSON report
# ---------------------------------------------------------------------------
$outDir = $OutputDirectory -replace "/", "\\"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$jsonPath = Join-Path $outDir "WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.json"
$report | ConvertTo-Json -Depth 20 | Set-Content -Path $jsonPath -Encoding utf8NoBOM

# ---------------------------------------------------------------------------
# Emit Markdown report
# ---------------------------------------------------------------------------
if (-not $JsonOnly) {
    $md = [System.Text.StringBuilder]::new()
    [void]$md.AppendLine("# Windows OpenClaw/Nollm Live Preflight Report")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- Schema: ``$($report.schema)``")
    [void]$md.AppendLine("- Generated: ``$($report.generated_at)``")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 1. Safety declaration")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("| Assertion | Value |")
    [void]$md.AppendLine("|-----------|-------|")
    foreach ($k in $report.safety.Keys) {
        [void]$md.AppendLine("| $k | $($report.safety[$k]) |")
    }
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 2. Observed facts")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- OpenClaw command: ``$(Get-NollmPublicPath -PortablePath $report.operator_private_paths.openclaw_command)``")
    [void]$md.AppendLine("- OpenClaw version: ``$($report.openclaw.cli.version.value)`` ($($report.openclaw.cli.version.status))")
    [void]$md.AppendLine("- Profile: ``$($report.openclaw.profile.selected_profile.value)`` ($($report.openclaw.profile.selected_profile.status))")
    [void]$md.AppendLine("- Config candidate: ``$(Get-NollmPublicPath -PortablePath $report.operator_private_paths.config_path)`` ($($report.openclaw.config.candidate_path.status))")
    [void]$md.AppendLine("- State candidate: ``$(Get-NollmPublicPath -PortablePath $report.operator_private_paths.state_dir)`` ($($report.openclaw.state.candidate_path.status))")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 3. Current memory ownership")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- plugins.slots.memory: ``$($report.openclaw.memory.plugins_slots_memory.value)`` ($($report.openclaw.memory.plugins_slots_memory.status))")
    [void]$md.AppendLine("- Selected memory provider: ``$($report.openclaw.memory.selected_memory_provider.value)`` ($($report.openclaw.memory.selected_memory_provider.status))")
    [void]$md.AppendLine("- Nollm memory companion: ``$($report.openclaw.memory.nollm_memory_companion_state.value)``")
    [void]$md.AppendLine("- Nollm memory provider: ``$($report.openclaw.memory.nollm_provider_state.value)``")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 4. Session/transcript location result")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- Transcript store status: ``$($report.openclaw.sessions.transcript_store_status.value)``")
    [void]$md.AppendLine("- Session index path: ``$(Get-NollmPublicPath -PortablePath $report.openclaw.sessions.session_index_path.value)`` ($($report.openclaw.sessions.session_index_path.status))")
    [void]$md.AppendLine("- Transcript root path: ``$(Get-NollmPublicPath -PortablePath $report.openclaw.sessions.transcript_root_path.value)`` ($($report.openclaw.sessions.transcript_root_path.status))")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 5. Legacy workspace memory metadata")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- MEMORY.md exists: ``$($report.workspace.legacy_memory_metadata.MEMORY_md.exists)``")
    [void]$md.AppendLine("- DREAMS.md exists: ``$($report.workspace.legacy_memory_metadata.DREAMS_md.exists)``")
    [void]$md.AppendLine("- memory/ directory exists: ``$($report.workspace.legacy_memory_metadata.memory_directory.exists)``")
    [void]$md.AppendLine("- Content never emitted: ``$($report.workspace.legacy_memory_metadata.MEMORY_md.content_not_emitted)``")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 6. Workspace bootstrap risk")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- Risk level: ``$($report.workspace.bootstrap_risk.risk_level.value)`` ($($report.workspace.bootstrap_risk.risk_level.status))")
    [void]$md.AppendLine("- Note: P1 Node-only probe is required to confirm actual prompt injection.")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 7. Python interpreter visibility")
    [void]$md.AppendLine("")
    foreach ($cand in $report.python.interactive_shell.candidates) {
        [void]$md.AppendLine("- $($cand.name): ``$($cand.probe.status)`` -> ``$(Get-NollmPublicPath -PortablePath $cand.probe.executable)``")
    }
    [void]$md.AppendLine("- Gateway Python: ``$($report.python.gateway_environment.value)`` ($($report.python.gateway_environment.status))")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 8. Gateway process observability limits")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- Process inspection: ``$($report.gateway_process.inspection_enabled)``")
    [void]$md.AppendLine("- Status: ``$($report.gateway_process.status)``")
    [void]$md.AppendLine("- Count: ``$($report.gateway_process.processes.Count)``")
    [void]$md.AppendLine("- Environment variables are not observable without explicit in-process probe.")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 9. P1 readiness")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- Status: ``$($report.readiness.p1_node_only_probe.status)``")
    [void]$md.AppendLine("- Blocking reasons: ``$($report.readiness.p1_node_only_probe.blocking_reasons -join ', ')``")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 10. P2 readiness")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- Status: ``$($report.readiness.p2_managed_python_probe.status)``")
    [void]$md.AppendLine("- Blocking reasons: ``$($report.readiness.p2_managed_python_probe.blocking_reasons -join ', ')``")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 11. Unknowns and next required evidence")
    [void]$md.AppendLine("")
    if ($report.unknowns.Count -eq 0) {
        [void]$md.AppendLine("- None recorded.")
    } else {
        foreach ($u in $report.unknowns) { [void]$md.AppendLine("- $u") }
    }
    [void]$md.AppendLine("- Required: P1 Node-only probe to confirm actual memory-slot behavior and workspace bootstrap sequence.")
    [void]$md.AppendLine("")

    [void]$md.AppendLine("## 12. Command ledger")
    [void]$md.AppendLine("")
    foreach ($cmd in $report.commands) {
        [void]$md.AppendLine("- ``$($cmd.command)`` -> $($cmd.status)")
    }
    [void]$md.AppendLine("")

    $mdPath = Join-Path $outDir "WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.md"
    $md.ToString() | Set-Content -Path $mdPath -Encoding utf8NoBOM
}

Write-Host "Preflight complete: $jsonPath" -ForegroundColor Green
if (-not $JsonOnly) {
    Write-Host "Markdown report: $mdPath" -ForegroundColor Green
}
