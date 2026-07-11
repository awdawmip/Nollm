# M1C1 Exact Geometry, Access Binding, and State Report

Date: 2026-07-11

## Verified Facts

- Core coverage is compiled from the finite registry for
  `eisenstein_exact_v1`, `aligned_baseline_v1`, and `dream_quasi_v1`.
- Coverage up uses layer delta `-1`; coverage down uses `+1`.
- The external audit example at layer 3, q 4, r -2 produces exact Q16 weights
  `21846, 21845, 21845` and the accepted up/down offsets.
- Six accepted profile/direction templates match the retained GRF fixtures.
- Core state embeds profile and kernel registry identity and rejects unknown
  profiles, coercive values, duplicate cells/atoms/bridges, and noncanonical
  bytes.
- Runtime state bytes equal the canonical store bytes after initialization,
  mutation, import, restore, and reopen.
- Access uses one canonical `HandleBinding` per handle with one current
  statement and a finite sorted supporting set.
- Recall distinguishes `binding_missing`, `evidence_missing`, and
  `evidence_payload_mismatch`; it never guesses from atom identity.
- Core plus binding mutations restore both pre-state byte snapshots on ordinary
  failures and raise `AccessConsistencyError` if rollback itself cannot finish.
- Boundary report records zero production violations and zero production
  cycles.

## Validation

```text
nollm-core = 13 passed
nollm-snapshot = 3 passed
nollm-trace = 1 passed
nollm-access = 11 passed
M0 = 18 passed
architecture/no-forbidden/hygiene = 8 passed
GRF = 112 passed
geometry parity = 6/6 passed
M1 explicit E2E = passed with NullTraceSink and FailingTraceSink
```

## Retained Boundaries

The old GRF tree remains a quarantined compatibility and regression asset. It
is not imported by active packages or Bare/Minimal distributions. Its accepted
coverage outputs are used only by the Lab parity executable.

## Limitations

Current Core and Access state remain single canonical files rather than
geometry-partitioned PB-scale storage. This stage does not validate LLM
placement quality, OpenClaw Live, History/Audit product behavior, corpus work,
or distributed transactions.
