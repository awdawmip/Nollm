# Nollm GRF Plugin Architecture

`nollm-grf` is a native OpenClaw plugin, not a memory provider. Hooks are short observers; capture and placement are separated. The six tools call a local JSON bridge only for explicit Core operations.

Placement follows `nollm_prepare_placement -> llm-task -> nollm_apply_placement`. The model decides only among bounded candidate identities and cells. Core validates the declared action and never derives semantic placement from hashes, scores, or global indexes.
