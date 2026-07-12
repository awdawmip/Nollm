# OpenClaw Runtime Discovery

Date: 2026-07-12

- Runtime: OpenClaw 2026.6.11 (`e085fa1`) on Windows 10.
- CLI: `C:\Users\Administrator\AppData\Local\Programs\nodejs\openclaw.cmd`.
- Node entry: `C:\Users\Administrator\AppData\Local\Programs\nodejs\node_modules\openclaw\openclaw.mjs`.
- Configuration: `C:\Users\Administrator\.openclaw\openclaw.json`.
- Extensions: `C:\Users\Administrator\.openclaw\extensions` plus explicit `plugins.load.paths`.
- LLM interface: `openclaw infer model run --json --model meituan/LongCat-2.0 --prompt <text>`.
- Envelope: `ok`, `capability=model.run`, `transport=local`, provider/model, and visible `outputs[].text`.
- Gateway: Windows Scheduled Task, port 18789; `gateway status/restart` are the lifecycle and diagnostic entry points.
- Plugin surface: `defineToolPlugin` and `plugins install --link`, `enable`, `disable`, `uninstall`, `list`, `validate`.
- Timeout behavior: the Windows launcher respawns Node with a larger stack. The Python adapter invokes the same installed Node entry directly so its bounded subprocess timeout controls the complete call.

The minimum clean probe returned `AOLD_CLEAN_PROBE_OK` from `meituan/LongCat-2.0`. Three obsolete Nollm plugins were removed from the host before live validation. Their source trees were not modified or reused.

Visible model output only is retained. Hidden reasoning is not requested or stored.
