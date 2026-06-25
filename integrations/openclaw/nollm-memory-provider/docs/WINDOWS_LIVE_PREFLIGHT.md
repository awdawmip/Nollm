# Windows OpenClaw/Nollm Live Preflight

**Scope**: P0-01 read-only runtime fact collection on a real Windows host.

This tool answers ten questions before any memory-slot cutover or Python sidecar work:

1. Which OpenClaw profile / state / config paths are actually in use?
2. Who is the current active memory owner?
3. What is the runtime state of memory-core, active-memory, nollm-memory-companion, and nollm-memory-provider?
4. How does OpenClaw discover local plugins?
5. Where is the current chat transcript stored (path metadata only)?
6. Are `MEMORY.md` / `memory/*.md` old memory notes or full transcripts?
7. Can OpenClaw workspace bootstrap inject `MEMORY.md` into prompts?
8. Which Python interpreters are visible from the interactive shell?
9. What Gateway process facts can be observed read-only?
10. Are the P1 Node-only and P2 managed-Python probes ready to start?

## Important constraints

The preflight runner is strictly read-only. It will **never**:

- Modify OpenClaw config.
- Restart, start, or stop the Gateway.
- Install, link, or uninstall plugins.
- Start any Nollm Python sidecar or worker.
- Read or emit chat transcript content.
- Read or emit `MEMORY.md` / `memory/*.md` / `DREAMS.md` content.
- Switch `plugins.slots.memory`.
- Create capture receipts, tombstones, or archives.

All Windows paths emitted in JSON, Markdown, or documentation are normalized to forward slashes (`/`).

## Usage

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File `
  integrations/openclaw/nollm-memory-provider/tools/windows-live-preflight.ps1 `
  -OutputDirectory "C:/Temp/nollm-preflight" `
  -OpenClawCommand "C:/path/to/openclaw.cmd" `
  -Profile "default"
```

If `-OpenClawCommand` is omitted, the script discovers `openclaw` from `PATH`.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `-OutputDirectory` | Yes | Only directory the script is allowed to write. |
| `-OpenClawCommand` | No | Absolute path to the OpenClaw executable or wrapper. |
| `-Profile` | No | OpenClaw profile name. Default: `default`. |
| `-ConfigPath` | No | Read-only candidate config path. |
| `-WorkspacePath` | No | Read-only candidate workspace path. |
| `-OpenClawStateDir` | No | Read-only candidate state directory. |
| `-NoProcessInspection` | No | Skip `Win32_Process` query. |
| `-JsonOnly` | No | Emit only JSON; skip Markdown report. |

The following parameters are intentionally **not accepted** in P0:

`-NollmDataRoot`, `-PythonCommand`, `-EnableNollm`, `-SwitchMemorySlot`, `-WriteConfig`, `-InstallPlugin`.

## Output files

In the directory specified by `-OutputDirectory`:

- `WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.json` — machine-readable report matching `preflight-report-schema.json`.
- `WINDOWS_OPENCLAW_NOLLM_PREFLIGHT_REPORT.md` — human-readable report with each fact marked `Observed`, `Inferred`, `Unavailable`, or `Blocked`.

## Report sections

The Markdown report follows this fixed order:

1. Safety declaration
2. Observed facts
3. Current memory ownership
4. Session/transcript location result
5. Legacy workspace memory metadata
6. Workspace bootstrap risk
7. Python interpreter visibility
8. Gateway process observability limits
9. P1 readiness
10. P2 readiness
11. Unknowns and next required evidence
12. Command ledger

## Path normalization

Input paths such as:

```text
C:\Users\Administrator\.openclaw\workspace
```

are normalized to:

```text
C:/Users/Administrator/.openclaw/workspace
```

Public-facing Markdown uses placeholders:

```text
%USERPROFILE%/.openclaw/workspace
```

Raw absolute paths are confined to the `operator_private_paths` section of the JSON report.

## Redaction

The report recursively redacts values whose keys contain:

```text
token, secret, password, authorization, api_key, apikey, cookie, credential, private_key
```

It also redacts common secret patterns such as:

```text
Bearer <...>
sk-...
ghp_...
github_pat_...
xox...
```

## Transcript and legacy memory semantics

- **Full conversation transcript** = records managed by OpenClaw's session/transcript store.
- **MEMORY.md / memory/*.md / DREAMS.md** = legacy workspace memory notes, not transcripts.

P0 does not claim that Nollm has taken over. It records observed facts and marks everything else `unavailable`.

## Windows Python rule

Windows runtime detection never defaults to `python3`. The script probes `py`, `python`, and `python3` launchers but records only absolute `sys.executable` values in canonical forward-slash form.

## Plugin config hierarchy

Plugin configuration belongs under:

```json
{
  "plugins": {
    "entries": {
      "nollm-memory-provider": {
        "config": { }
      }
    }
  }
}
```

Do not place config keys directly under the plugin entry object.

## F0-05 status

F0-05 host-loader and Python sidecar work is paused until P0-01, P1, and P2 are complete and manually reviewed.

## Tests

Run the non-Windows static tests:

```powershell
node --test integrations/openclaw/nollm-memory-provider/tests/*.test.mjs
```

Live Windows execution must be performed on a real Windows host with OpenClaw installed.

## Next steps

- **P1**: Node-only memory-slot probe in an isolated OpenClaw profile.
- **P2**: Managed Python worker probe with an absolute `python.exe` and `shell:false`.
