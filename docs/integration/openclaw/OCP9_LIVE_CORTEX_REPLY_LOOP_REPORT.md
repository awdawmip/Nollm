# OCP9 Live Cortex Reply Loop Report

Status: completed with one residual primary UX defect.

OCP9 connects a blind OpenClaw primary agent to Nollm through Active Memory. The primary workspace has no source MEMORY.md injection, no memory search provider, and no source bootstrap. Active Memory is configured with the OCP9 geometry-only tool surface:

- `nollm_memory_status`
- `nollm_field_overview`
- `nollm_open_well`
- `nollm_surface`
- `nollm_focus`
- `nollm_drift`
- `nollm_read`
- `nollm_recall_trace`

Legacy `nollm_memory_recall/search/get`, raw `memory_search/get`, raw read/write/edit/exec, vector, graph, and embedding paths remain excluded.

## Live Result

The live Dreamer produced field revision `rev_4d7911e511727c82` from the read-only OCP9 fixture. Live Cortex navigation then answered:

- Mira Chen coordinates Project Atlas.
- Blue Whale was Atlas's topology experiment in the first revision.
- Lighthouse was Atlas's OpenClaw integration branch.
- The coffee machine is on the second floor.

After the fixture changed Blue Whale to a geometry execution experiment, the old field reported `field_stale: true`. Active Memory returned `field stale - refresh required` instead of presenting stale facts. A forced Dreamer refresh produced `rev_ea65eb9d080b82fd`; a new Cortex turn answered that Blue Whale is Atlas's geometry execution experiment.

## Revision Binding

Old well `well_4c1838ef6cf5285d` stayed bound to `rev_4d7911e511727c82` and continued to read `Blue Whale is Atlas's topology experiment.` after refresh. New well `well_2b17d4960120bc52` bound to `rev_ea65eb9d080b82fd` and read `Blue Whale is Atlas's geometry execution experiment.`

## Residual Defect

For the Atlas update prompt, the Cortex digest correctly said that no current Atlas status or progress record was found. The blind primary still phrased the final reply as "Atlas is still advancing." This is a primary-response grounding defect, not a Core/Cortex geometry defect. The evidence manifest records it as `primary_over_answering_residual`.

## Evidence

See `docs/integration/openclaw/evidence/ocp9_live_cortex_reply_loop_20260621.json`.
