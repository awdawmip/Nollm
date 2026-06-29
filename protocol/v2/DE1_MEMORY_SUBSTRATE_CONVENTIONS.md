# DE1 Memory Substrate Conventions

The repository path uses `evidence/`, but DE1 uses the architectural meaning
Memory Substrate / Epistemic Core. The module stores memory material with clear
epistemic separation; it is not a legal evidence, authentication, or anti-tamper
system.

`UsageState` means current use posture:

- `tentative`: retained but provisional for current work.
- `active`: usable as default current working material.
- `retired`: historically retained but not current default material.
- `rejected`: retained as withdrawn, counterexample, or audit material.

These states are not truth values, source authentication, or permanent human
confirmation. Explicit transitions can restore material, and every accepted
transition appends a ledger event.

DE1 IDs are caller-provided stable record identities. They are not credentials.
Payload hashes are deterministic equivalence keys for idempotency and reports;
they are not signatures.

Within a store root, durable record IDs are global across shards,
interpretations, revision threads, and usage-state transitions. References in
revision and usage state therefore resolve to one epistemic object rather than
depending on bucket order.

Ledger closure means that DE1 can explain every accepted durable object through
one corresponding ledger event, and every ledger event through one object. It is
ordinary format validation, not repair, authentication, or tamper resistance.
