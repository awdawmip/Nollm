# DI1 Integration Shell Contract

DI1 defines a host-controlled, transport-neutral, read-only typed shell over
the sealed DR1 recall resolver.

DI1 supports only:

```text
capabilities
recall
```

DI1 does not implement JSON input parsing, HTTP, WebSocket, gRPC, CLI, daemon,
OpenClaw, runtime hooks, persistent sessions, caches, databases, telemetry, or
write paths.

## Typed Inputs

The host must provide all recall inputs in process:

- a DC1 `CompiledQueryProbe`;
- a finite DR1 `RecallUniverse`;
- a DE1 `MemorySubstrateStore` public reader;
- an optional caller-owned `RuntimeTimeResolution`;
- a fixed host-owned `RecallPolicy`.

DI1 does not accept raw natural-language requests, filesystem paths, store
roots, universe selectors, chart/cell/seed directives, internal tie-break
controls, relative-time calendar rules, policy overrides, debug flags, or write
instructions.

## Recall Boundary

DI1 must call the DR1 public facade `resolve_recall`. It must not compile
queries, construct or scan a `RecallUniverse`, import recall internals, read
unselected records, mutate upstream stores, or persist any request or digest.

DR1 non-resolved outcomes such as `deferred`, `insufficient_evidence`,
`budget_exhausted`, and `rejected` are successful transport responses. Invalid
typed invocation or context shape is a DI1 public error.

## Public Recall Envelope

DI1 maps the ephemeral DR1 digest to a JSON-safe public mapping. The public view
may contain:

- request echo and operation echo;
- digest identity, query probe identity, status, and ephemeral marker;
- primary and contextual DreamShard evidence selected by DR1;
- original DreamShard content and public origin/time context;
- current usage state;
- matched axis identifiers;
- fixed discrete selection basis labels;
- Interpretation and Revision records as contextual views only;
- sanitized warnings and discarded diagnostics.

The public envelope must not expose raw `OriginDescriptor.reference`,
`OriginDescriptor.context_reference`, `OriginDescriptor.role_label`,
`TemporalContext.source_time_expression`, or `TemporalContext.locale_hint`.
These free-text provenance fields are projected as deterministic state labels:

```json
{
  "origin": {
    "kind": "user_utterance",
    "reference_state": "absent | present_redacted",
    "context_reference_state": "absent | present_redacted",
    "role_state": "absent | present_redacted"
  },
  "temporal_context": {
    "captured_at": "RFC3339 string | null",
    "reference_instant": "RFC3339 string | null",
    "source_time_expression_state": "absent | present_redacted",
    "locale_hint_state": "absent | present_redacted"
  }
}
```

`kind`, `captured_at`, and `reference_instant` may remain public because they
are discrete enum or DE1-validated RFC3339 values. Free-text provenance is not
hashed, truncated, basename-extracted, classified by string pattern, or restored
because it looks harmless.

The public envelope must also not expose internal tie-break state, structure
metrics, traversal identifiers, cell or chart references, cover or trace
identifiers, kernel identifiers, route details, filesystem locations, store
roots, Python exception types, traceback text, or object representations.

Interpretation context must not replace DreamShard content. Revision context
must not assert truth, falsity, or a unique current fact.

DE1 `basis_refs` and `context_refs` are path-safe record references. They are
not DI1 filesystem provenance fields. Any future public/private provenance
classification for those references requires a separate task; DI1.1 does not
invent source ontology or string classification rules.

## Determinism And Side Effects

The same typed invocation and context must produce canonical-equivalent public
mapping. DI1 must not read the system clock, environment, network, subprocesses,
runtime state, databases, caches, sessions, or global memory. DI1 owns no
durable object.

This projection is not a security sandbox, permission system, signature model,
source authenticity judgment, privacy classifier, or content redaction system.
DreamShard content and selected Interpretation statements remain verbatim.
