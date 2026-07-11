# M1C2 Complete Kernel, Canonical Evidence, and Transaction Report

Date: 2026-07-11

## External Reproductions Closed

- Lateral is present in the active registry; all `3 x 3` templates carry the
  complete retained contract.
- Lateral ring 2 is rejected before expansion because fanout 12 exceeds the
  default hard limit 7.
- Semantic-noncanonical cell, atom, and bridge ordering and empty cells are
  rejected.
- Bad direct anchor/bridge types are rejected before Core writes.
- MemoryStatement and Evidence decode perform no numeric or boolean coercion.
- Evidence files require exact fields and byte-for-byte canonical encoding.
- Missing Evidence no longer prevents explicit Handle forget.
- Same-process Access transactions share a canonical workspace lock, so a
  failed call cannot roll back another call that returned successfully.

## Windows Results

```text
nollm-core = 21 passed
nollm-snapshot = 4 passed
nollm-trace = 1 passed
nollm-access = 27 passed
full geometry parity = 9/9 passed
M1C2 structured E2E = passed
```

The Final Gate additionally records M0, architecture/hygiene, GRF, boundary,
compileall, diff, and bundle results after all tracked files are finalized.

## Canonical State

Every accepted Core payload follows one path: strict JSON decode, exact object
validation, runtime reconstruction, authoritative re-encoding, and byte
equality. Store public read/write, reopen, import, and Snapshot restore use that
same semantic validator. Cross-cell reuse of `atom_id` remains allowed because
`AtomHandle(address, local_atom_id)` is the unique locator; no global route is
created.

## Concurrency Scope

The guarantee covers threads and multiple AccessRuntime/FileEvidenceStore
instances in one Python process that resolve to the same Windows workspace.
Lock order is Access workspace lock, then Core lock, then Binding/Evidence file
operation. Multi-process coordination, process-crash recovery, databases,
event sourcing, and distributed transactions are out of scope.

## Legacy And Environment

Legacy GRF is used only by `run_geometry_parity.py` as the retained oracle for
profiles, nine templates, metadata, residuals, expansion, negative coordinates,
and phase preservation. No active package imports Legacy.

No OpenClaw Live, model, corpus, remote repository, History/Audit product, or
PB-scale work was executed.
