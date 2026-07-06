# HAG1 Integration Note

HAG1 is a file-first gateway for trusted hosts that already own an HX1 workspace. It is intentionally separate from HCG1 capture/read and from the V1 CLI.

Public dependency boundaries:

- Uses `nollm.dream_geometry.host_execution` for `execute_host_plan`, bindings, context, and receipt serialization.
- Uses `nollm.dream_geometry.batch_admission` for structured promotion decisions.
- Uses `nollm.dream_geometry.admission` for admission requests and public placement replay parsing.
- Uses `nollm.dream_geometry.capture` for public candidate state lookup.
- Uses `nollm.dream_geometry.evidence` for explicit DreamShard reads.
- Uses CX2-compatible mapping plans so HX1 performs public plan validation.

The CX2 projection uses declared `dac_` and `shard_` refs while the HX1 binding also carries the actual CI1 candidate and DreamShard identity. This preserves CX2 conformance without rewriting CI1/HCG1 IDs such as `dac:...` and `shard:ci1:...`.
