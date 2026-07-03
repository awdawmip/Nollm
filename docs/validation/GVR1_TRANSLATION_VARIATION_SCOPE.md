# GVR1 Translation Variation Scope

GVR1 is a pure synthetic geometry validation over the sealed GPR1-C1 baseline:

`c48ceba98e5d5197d16f91c3bad507b2ceaed242`

It samples only parameter B, the current engineering baseline, across the fixed finite layer window `0..16`.

## Fixed Window

- `LAYER_GAPS = (1, 2, 4, 8, 16)`
- `base_layers(gap)=range(0, 17-gap)`
- `TRANSLATION_RADIUS = 1`
- `TRANSLATION_OFFSETS = disk(AxialCoord(0, 0), 1)`
- `TARGET_RADIUS = 4`
- `THRESHOLD = 1e-9`
- `TOLERANCE = DEFAULT_TOLERANCE`
- `DEFAULT_PHASE_SAMPLES` and `LAYER_PHASE_POLICIES` are read from sealed DG1 APIs.

Each row samples `7 * (17-gap)` real DG1 coverage distributions.

## Boundary

GVR1 calls sealed DG1 public geometry APIs and produces only a derived Markdown validation report. It does not modify DG1, DG2, production geometry, profile IDs, beta, theta, phase policy, translation policy, memory, capture, admission, assembly, recall, adapters, runtime, OpenClaw, network, database, cache, LLM, NLP, embedding, or semantic search behavior.

The result is a finite seven-offset translation-variation observation. It is not an all-plane theorem, not an exact algebraic proof, and not production profile selection.
