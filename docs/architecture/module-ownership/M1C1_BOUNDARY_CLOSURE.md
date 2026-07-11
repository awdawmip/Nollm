# M1C1 Boundary Closure

M1C1 preserves the M1 package boundary result while correcting the behavior
behind it.

```text
production violations = 0
production cycles = 0
migration dependencies = 9
```

The active `nollm-core` package now owns its exact integer profiles, coverage
templates, fixed-point normalization, and kernel registry. It does not import
the quarantined GRF tree. The GRF implementation remains a regression and
parity input only.

The active `nollm-access` package owns canonical Evidence-to-Handle bindings
and exception-atomic coordination through public Core state ports. Core does
not import Access, Snapshot, Trace implementations, or Legacy. Snapshot and
Trace continue to bind only through public Core contracts.

The duplicate, unreachable GRF classification branch in the ownership
generator was removed. Zero production findings are therefore supported by
active package imports and tested replacements, not by a second owner or
lifecycle suppression path.
