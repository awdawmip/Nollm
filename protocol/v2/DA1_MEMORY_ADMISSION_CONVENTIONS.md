# DA1 Memory Admission Conventions

- Admission IDs are host supplied and stable. The reference fixture uses
  `adm_` prefixes.
- Placement plan IDs use `apl_` prefixes.
- DA1 admits exactly one GrowthStep per AxisRay.
- Every admitted axis has exactly one matching `AxisPlacement`.
- DA1 uses only `CoverageDirection.fine_to_coarse`.
- The fixed Field profile is `da1_sealed_default_v1`.
- Seed mass is `1.0`; genericity, ambiguity, and conflict are `0.0`;
  stability epochs are `1`; state is `accepted`.
- Cover and Gravity use sealed DG2 default policies.
- Crystallization, compaction, automatic placement, Query, Recall, DI1,
  runtime integration, OpenClaw, network, databases, caches, and concurrent
  writers are outside DA1.
