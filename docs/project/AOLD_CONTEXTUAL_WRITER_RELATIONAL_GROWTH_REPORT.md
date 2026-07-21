# AOLD Contextual Writer And Shared-Retrieval Growth Report

Date: 2026-07-21

Status: `AOLD_CONTEXTUAL_RELATIONAL_GROWTH_IN_PROGRESS_AT_cda2952`

Input checkpoint: `c40f8bf6a5be6184e5e56236c96d2817fed4bee5`

## Checkpoint Reclassification

The c40f8bf reliability fixes remain accepted. Its live one-cell conclusion is
withdrawn: every Progressive Atlas region reused the local identity
`progressive-entry:0`, and fast Recall reduced all regions through a single-key
dictionary. The Provider therefore saw one surviving entry rather than the
complete Atlas.

## Deterministic Gates

- Selectable entry identity now binds Atlas fingerprint, region identity, and
  canonical GeometryAddress.
- Progressive Atlas pages reject duplicate selectable identities.
- Fast Recall reports Atlas, prompt, and duplicate entry counts and never
  silently overwrites a candidate.
- The nine-region collision fixture exposes nine unique IDs and can select all
  nine Cells independently.
- Capture batches are session-partitioned.
- Writer context is strictly prior, chronological, same scope/workspace/session,
  bounded to four Captures and 6000 characters, and does not advance context
  Capture state.
- Contextual Writer v2 records exact Evidence spans, resolved-reference basis,
  direct queries, and broader entry queries.
- Unsupported absolute dates fail deterministic validation.
- Cartographer resolves only entry queries and is taught shared retrieval
  neighborhoods rather than pre-existing answers.
- Necessary context Capture Evidence refs persist on the MemoryStatement while
  source Capture ownership remains unchanged.

## Current Verification

- Entry collision focused tests: `24 passed`.
- Access and OpenClaw Python: `178 passed`, 8 deprecation warnings.
- OpenClaw Node: `50 passed`.
- Context/provenance focused tests: `16 passed`.

## Outstanding Live Gate

The isolated v6 nine-fact OpenClaw run, related-growth threshold, wrong-date
check, distinct Reader entries, three target-hidden paths, restart, NONE,
frozen Evidence, final governance and bundle verification remain pending.

No Core, multi-cell, multi-entry Recall, Topic/Entity, graph, vector, embedding,
or persistent query/fact mapping is authorized.
