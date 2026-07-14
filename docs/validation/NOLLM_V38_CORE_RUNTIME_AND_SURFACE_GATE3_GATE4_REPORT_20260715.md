# V3.8 Core Runtime and Surface Gate 3/4 Report

Date: 2026-07-15
Input checkpoint: `53d31104aac2ef7d61c9bb097c33d302d2a281b8`

## Core Runtime

- `default_dream_v1` adjacent-layer coverage is computed from the complete
  `GeometryAddress` by a Core-owned Decimal polygon runtime.
- Core imports neither Lab nor reference implementations and uses no binary
  float in the physical coverage path.
- Default-profile phase-only `coverage_up` and `coverage_down` templates are no
  longer active registry entries. Legacy profiles and lateral templates remain.
- Candidate radius is the conservative adjacent-layer physical bound of four;
  observed positive fanout remains within the canonical limit of seven.
- All positive overlap members receive positive Q16 weight. Sum weight is
  `65536`, normalization residual is `0`, and maximum quantization residual is
  one Q16 unit.
- The derived cache is bounded and clearable. It is absent from canonical state.
  Mutation, export, close, reopen, cache clearing, and replay preserve results.

The full Core/Oracle A/Oracle B matrix covered 1,296 samples. Support mismatch
and positive-weight-on-zero-overlap counts were both `0`. Maximum source-share
error was `5.151057873284273813269880266726260565731665204987007503043e-15`
against Oracle A and `0` against Oracle B. Maximum Q16 error was `1`.
Cache-clear replay digests were identical:
`7b037c6fe44a4fad28adbe70d014f2380a5964f763fa9d28f00ccc9e1d067e9a`.

The full matrix completed in 111.3 seconds on the Windows validation host.
Performance is recorded as required and is not used as a correctness shortcut.

## Surface

- Order 0 projects every native physical layer through the same coverage
  runtime and retains every positive overlap member as source provenance.
- Orders 1 through 8 use the same runtime; nearest-only and at-most-two-target
  projection logic was removed.
- Integer remainder distribution preserves aggregate mass at every order.
- Observation area strictly increases at every order.
- Dense radius-5 occupancy coarsened from 91 to 85 cells.
- Dense radius-8 occupancy coarsened from 217 to 91 cells and selected order 3
  within budget.
- Sparse occupancy was not forced to decrease.
- The independent overflow fixture selected hard maximum order 8 with
  `overflow=true`; within-budget fixtures remained `overflow=false`.

## External Evidence

| Evidence | SHA-256 |
| --- | --- |
| `C:\Users\chaos\nollm_v38_gate3_core_runtime.json` | `7484f3bfcd426e098d5e56af59479e369d85b2b026377b5055bd6e7539d3cd05` |
| `C:\Users\chaos\nollm_v38_gate4_surface.json` | `943c6aa61b748762e2823fb513ab3f4b5e9190361ba5b2531e78b3024e1395eb` |
