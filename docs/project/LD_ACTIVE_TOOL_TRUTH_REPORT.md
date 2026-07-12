# LD Active Tool Truth Report

Date: 2026-07-12

Input baseline: `0735806c303ce7d1f61e0c38412b3784a31f16b9`

Validated code commit: `7ff9690edeca71806bf5783787ef81367b9eb167`

Validated code tree digest:
`b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27`

## Classification Result

The withdrawn M1-C7/M1-C8 adversarial scripts were moved without content loss
to `lab/nollm-lab/history/m1` and classified `LAB / HISTORICAL`. They remain
available for provenance but do not define an ACTIVE capability. No Core,
Snapshot, Trace, or Access public API was expanded for them.

Current generators, geometry libraries, M1 validation entrypoints, fixtures,
and datasets are explicitly classified. The manifest generator does not infer
ACTIVE status from historical stage numbers or filenames.

## Machine Gates

- Ownership manifest: 1485 tracked files after this report and boundary
  evidence are included; unclassified 0.
- ACTIVE Lab contract gate: 6 tests passed; private submodule imports 0;
  missing public root symbols 0; import failures 0.
- Boundaries: production violations 0; production cycles empty; migration
  findings 7 and explicitly outside the production gate.
- Package tests: Core 39, Snapshot 7, Trace 3, Access 32.
- Governance tests: M0 38; architecture and hygiene 8; GRF 112.
- Geometry parity: 9/9. Core capability: 25/25. Minimal E2E: passed.
- Compiled template artifact SHA-256:
  `21659434328e457e0d868ddc1dcbf64484739ffeb64eb61eb62197616ddf0eba`.
- Compileall and `git diff --check`: passed.

## Progress Truth

Previous task actual vector:

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +0~5% | DISTRIBUTIONS +0~5%
```

LD expected and actual vector:

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%
```

Every LD module deviation is zero. Actual completion is Core 80%, Snapshot
50%, Trace 40%, Access 60%, History 10%, Audit 10%, OpenClaw 25%, Lab 55%, and
Distributions 45%. Confidence is high for Core, Lab, and Distributions;
medium-high for Snapshot and Access; medium for Trace; medium-low for OpenClaw;
and low for unimplemented History and Audit.

## Limits

OpenClaw Live, real LLM placement, cross-process recovery, memory quality,
corpora, PB scale, installers, and version negotiation remain unvalidated.
The next candidate action requires a separately approved taskbook. The exact
delivered HEAD and bundle digest are recorded by delivery verification.
