# DG1 Geometry Kernel Scope

DG1 implements only deterministic V2 geometry primitives in `nollm.dream_geometry.geometry`:

- immutable numeric geometry objects;
- axial/cube hex-grid operations;
- local chart coordinate maps and phase diagnostics;
- convex polygon intersection for hex cells;
- orientation-preserving similarity transforms and cycle residuals;
- directed coverage kernels, residual mass, and partition validation;
- finite-window anti-resonance metrics and parameter schedules.

DG1 explicitly does not implement:

- Field Dynamics, Growth Trace persistence, Coarse Cover state, or gravity;
- Cortex semantic compilation;
- Query Probe Recall or Recall Resolver;
- Adapter, CLI, JSON tool, OpenClaw, sidecar, native memory, memory provider, trial, rollback, or runtime behavior;
- final parameter selection;
- exact algebraic-number geometry;
- unbounded atlas merge.

The V2 geometry package must remain import-isolated from V1 modules, OpenClaw modules, Field, Cortex, Recall, Adapters, and runtime code.
