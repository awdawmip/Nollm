# Nollm Cortex Recall Spine

OCP6R primary read path:

```text
orient -> surface -> focus -> drift/return -> compose_digest
```

OpenClaw Active Memory acts as the read-side Cortex. It should use only the Nollm navigation tools for the Nollm path:

- `nollm_orient`
- `nollm_surface`
- `nollm_focus`
- `nollm_drift`
- `nollm_read`
- `nollm_compose_digest`

Rules:

- inspect coarse surface before focusing;
- stop at sufficient scale;
- label lateral findings as lateral;
- return to the entry task;
- output `NONE` when the field lacks useful material;
- do not treat `memory_search` / `memory_get` as the Nollm internal model.

