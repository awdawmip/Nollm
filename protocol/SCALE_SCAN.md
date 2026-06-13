# Scale Scan

Recall is scale scan, not tree descent.

LLM/Nollm Cortex scans linearly downward across scales.

At each layer it re-evaluates active anchor fields.

If another field becomes stronger, it may shift laterally.

It stops when sufficient scale is reached.

## Complexity

Approximate runtime reading cost: `O(b × S)`, where `b` is per-layer candidate width and `S` is task-required scale depth.

This is not full-library `O(N)` scan.

## Runtime Status

The current reference CLI approximates this concept with deterministic `orient -> surface -> focus -> recall`. It does not implement geometry runtime behavior yet.

P5.4 stores and validates optional `scale_links` metadata with the keys `coarser`, `finer`, `overlaps`, and `recovery`.

Each value is a list of non-empty card IDs or memory addresses. Scale links are not a tree and do not use parent, child, children, or leaf semantics.
