# V3.8 Translation-Covariant Oracle Gate 2 Report

Date: 2026-07-15
Input checkpoint: `ae576ce078eb9795a4dcff82c6f6640d454da22a`

## Result

- Oracle A remains the unchanged historical float implementation.
- Oracle B is an independent Decimal implementation at precision 80 and does
  not import Oracle A or the existing Lab physical-geometry implementation.
- The matrix covered 1,296 samples across all eight phases, both adjacent-layer
  directions, negative coordinates, and non-origin `q/r` translations.
- Only 16 samples used the origin.
- Oracle A/B support mismatch count: `0`.
- False-negative count: `0`.
- Positive-weight-on-zero-overlap count: `0`.
- Maximum source-share error: `5.151057873284273813269880266726260565731665204987007503043e-15`,
  below the declared `1e-12` bound.
- Maximum Q16 error: `0`, below the declared one-unit bound.
- Maximum corrected Q32 world-transform error:
  `3.096758209195145724312047789352024012015621913707040327823641459679650e-9`,
  below the declared `1e-8` bound.
- Phase-only support differed for 1,232 samples, disproving address-independent
  phase-only coverage reuse.

The corrected Lab axial transform is derived as target-chart inverse composed
with source-chart world transform. The production compiler does not import or
execute Oracle B; Core runtime implementation remains Gate 3 work.

## Evidence

External canonical JSON:
`C:\Users\chaos\nollm_v38_gate2_oracle.json`

SHA-256: `7e9804a2244b5eb7daa5f3f82dc127c6ceddfa52ea5518db7c4da9d6e23e2507`
