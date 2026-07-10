# NOLLM GRF4 Host Integration Report

The File Adapter, declared OpenClaw V2 adapter, and declared Codex adapter
each ran capture, place, admit-existing-placement, and shard recall in separate
workspaces through `grf_host_v1`.

All three selected the same evidence identity:

`shard:grf:2d5942e0ad6fd68f966d3372`

All three returned the same source fallback reference with that identity.
The declared adapters only load capability configuration and delegate mapping
to the File Adapter; they do not write evidence, place, admit, or alter recall
results directly.

GATE_B_PASS and GATE_C_PASS. Identity isolation is preserved because each host
uses its own workspace and distinct host request IDs while the Core-generated
evidence identity remains deterministic for the shared capture input.
