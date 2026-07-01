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

The public envelope must not expose internal tie-break state, structure
metrics, traversal identifiers, cell or chart references, cover or trace
identifiers, kernel identifiers, route details, filesystem locations, store
roots, Python exception types, traceback text, or object representations.

Interpretation context must not replace DreamShard content. Revision context
must not assert truth, falsity, or a unique current fact.

## Determinism And Side Effects

The same typed invocation and context must produce canonical-equivalent public
mapping. DI1 must not read the system clock, environment, network, subprocesses,
runtime state, databases, caches, sessions, or global memory. DI1 owns no
durable object.

