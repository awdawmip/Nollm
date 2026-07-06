# HCG1 File-First Capture Gateway

HCG1 is a local file-first host capture gateway.

It is invoked as a standalone script:

```powershell
python reference/python/scripts/run_nollm_host_capture_gateway.py capture --workspace <workspace> --request <capture.json>
python reference/python/scripts/run_nollm_host_capture_gateway.py read --workspace <workspace> --request <read.json>
```

The gateway reads the request file, emits exactly one JSON envelope to stdout,
and exits with code `0` for `ok=true` or `2` for `ok=false`.

HCG1 only performs host-explicit Capture and explicit physical visibility read.
It does not integrate with OpenClaw, V1 CLI, tool manifests, network services,
daemon processes, agent runtimes, semantic recall, automatic admission, or
global captured-pool discovery.

## Capture

The capture request must provide a CI1-shaped `CaptureRequest` and
`CapturePolicy`. HCG1 maps those values into a capture-only CX2 plan and calls
HX1 `execute_host_plan`.

The capture path accepts `captured` and `persistent` policies with
`session_window`, `source_window`, or `persistent_explicit` visibility. HCG1 v1
rejects `ephemeral` and `current_turn` because there is no durable local
gateway read contract for those modes.

## Read

Read requests are selector-only:

- `session_window` reads by explicit `context_ref`;
- `source_window` reads by explicit `context_ref`;
- `persistent_explicit` reads by explicit `shard_ids`.

HCG1 read is not semantic recall. It does not accept query text, embeddings,
keywords, admission IDs, field policy, recall policy, limits, runtime values,
session handles, paths, URLs, or commands.

## Failure Shape

Failures are stable JSON envelopes:

```json
{"ok":false,"operation":"capture","request_id":"...","error":{"code":"HCG_INVALID_REQUEST","message":"request rejected"}}
```

The envelope intentionally does not expose Python tracebacks, module paths, or
workspace paths.
