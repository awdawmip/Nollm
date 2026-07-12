# AL Statement Formation Task Report

Date: 2026-07-12

Input baseline: `3528c0130a2f29987e06105753310d3b2a592a2a`

Core validated code commit: `7ff9690edeca71806bf5783787ef81367b9eb167`

Core validated tree digest:
`b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27`

Access Statement Formation validated code commit:
`1cad3f756528d91e1d88dc443357cc46ae2dac52`

Access Statement Formation Git-blob tree digest:
`9a62882d5b14a8d1e034a1032710d7a8a8eb91236f35a1eb38d99fd00e4525b9`

The Formation digest covers committed `nollm-access` source and tests plus the
Statement Formation Lab directory. Later delivery documentation does not alter
those 34 files.

## Progress

Expected and actual vector:

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +10% | DISTRIBUTIONS +5%
```

Measured deviation is zero. Completion changes are Access 60% to 70%, Lab 55%
to 65%, and Distributions 45% to 50%; all other module percentages are
unchanged.

## Access Contract

The package root exports Raw Evidence, Unicode code-point span, selection,
request, decision, formed statement, actor Protocol, validation, and assembly
contracts. Formed output wraps the existing `MemoryStatement`; provenance stays
outside Core. Formation is explicit and never invokes capture or placement.

## Corpus And Fixtures

- Cases: 126; categories: 14.
- Languages: Chinese 42, English 42, mixed 42.
- Splits: development 84, held-out 42.
- Outcomes: formed 117, defer 9; Gold statements 162.
- Gold boundary validity 1.0; overlap, text mismatch, and unknown fields 0.
- Perfect fixture: every applicable metric 1.0, hallucinated text 0.
- Off-by-one: accepted as evidence-faithful but exact span metrics degrade.
- Nine malformed or conflicting proposal classes are rejected.

## Limits

No model was called. Meaningful boundary selection, real Host integration,
placement, recall quality, OpenClaw Live, cross-process recovery, memory
quality, corpora beyond v1, PB scale, installers, and version negotiation remain
unvalidated. A next action requires a separately approved taskbook.

## Verification

- Manifest: 1505 tracked rows, unclassified 0; Lab assets 571; gated assets
  141/141.
- Boundary: production violations 0, production cycles empty, migration
  findings 7.
- Package tests: Core 39, Snapshot 7, Trace 3, Access 50.
- Governance and compatibility: M0 45, architecture 8, GRF 112.
- Geometry parity 9/9, Core capability 25/25, Minimal E2E passed.
- Corpus and fixture `--check`, compileall, and `git diff --check` passed.
