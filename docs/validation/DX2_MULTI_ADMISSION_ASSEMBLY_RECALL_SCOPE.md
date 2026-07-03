# DX2 Multi-Admission Assembly-to-Recall Scope

DX2 is validation-only. It verifies a host-explicit synthetic path:

```text
CI1 CaptureIngress
-> BA1 BatchAdmissionCoordinator
-> DA1 AdmissionRecord
-> DF1 explicit finite assembly
-> DR1 resolve_recall
-> DI1 IntegrationShell public envelope
```

Allowed changes are limited to DX2 fixtures, tests, validation runner, protocol
note, delivery receipt, baseline report, and roadmap status.

DX2 does not modify sealed production implementation and does not add LLM, NLP,
embedding, semantic search, runtime, OpenClaw, CLI, network, database, cache,
global discovery, global Field, automatic admission, or real memory integration.

The synthetic set is A/B/C/D:

- A and B are captured as deferred CI1 candidates and admitted through BA1.
- C is captured/deferred but not admitted.
- D is admitted through the normal public DA1 path but omitted from the BA1
  receipt admission IDs used by DF1.

DF1 input is only the two admission IDs returned by the BA1 receipt. Assembly
creates call-local in-memory values and writes no durable field, assembly, or
recall objects.
