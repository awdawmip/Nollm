# DG2 Field Dynamics Scope

DG2 implements deterministic Field Dynamics over sealed DG1 geometry outputs.

It includes:

- Growth Trace seed normalization and `K_up` propagation;
- explicit residual accounting;
- local Coarse Cover aggregation inside one chart fingerprint and one cell;
- versioned stability eligibility and explicit crystallization boundary;
- internal Gravity Snapshot calculation from stable / crystallized covers;
- lossless Trace compaction views.

It excludes:

- Cortex proposal generation;
- Query Probe and Recall Resolver;
- runtime, OpenClaw, adapter, CLI, JSON tool, or memory integration;
- Evidence, Card, Ledger, or Dream Shard persistence;
- final beta / theta / phase selection;
- global atlas merge, chart fitting, or DG1 geometry changes.
