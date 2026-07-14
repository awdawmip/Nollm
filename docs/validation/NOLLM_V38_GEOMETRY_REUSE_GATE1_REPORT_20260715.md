# V3.8 Geometry Reuse Gate 1 Report

Date: 2026-07-15
Input HEAD: `ac8ebaa44cda35e1d2f73e0bfc95055bae425a86`

## Result

- `tools/verify_reusable_geometry_assets.py`: 17/17 assets matched.
- DG1 fast geometry suite: 46/46 passed.
- Historical Oracle A source and fixture bytes were not modified.
- The five full Windows runners completed successfully.

External derived reports under `C:\Users\chaos\nollm_v38_gate1_outputs`:

| Runner | SHA-256 |
| --- | --- |
| GVR1 translation variation | `06d01f464a871c9847f58c2165326e10330987f034d9bc2ecbbccdb6b2868cb0` |
| GRA1 rotation-scale resonance | `8f16323a76f71dd15490f5cbf9cff3358020eb3386d1f3405e4264de6592304d` |
| GRC1 resonance-conditioned coverage | `cc3ffed1f1b84d3f8e7ce553be46e8f0cfca05fcd6d3bad1c1dc74bd7d38cb04` |
| GKD1 bidirectional coverage | `f424a2f9bfd2cd414ba67754263dbdd8bde1246c8fe5f3545f5084eea9218276` |
| GPR1 geometry profile regime | `09c128dff42a5ea89ad2981f65226d3e736e498343f744a5f6688d7ff24d71f6` |

## Classification

- `REUSE_AS_ORACLE`: historical chart, hexgrid, polygon, coverage, schedules,
  transform, and metrics modules.
- `PORT_WITH_ADAPTATION`: transform, candidate disk, clipping, overlap,
  directed mass/residual, translation stencil, and metrics concepts.
- `REFERENCE_ONLY`: finite historical windows and their measured conclusions.

The historical implementation remains an independent float64+tolerance Oracle.
Production modules must not import it. Gate 2 must add a separately derived
Decimal/interval Oracle before production geometry changes.
