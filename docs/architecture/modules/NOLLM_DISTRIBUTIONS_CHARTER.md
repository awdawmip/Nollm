# Nollm Distributions Charter

Purpose: declare installable combinations without business logic.

- Persistent state: package/version lock metadata only.
- Temporary state: build assembly metadata.
- Public API: manifests for bare, minimal, OpenClaw, debug, and audited variants.
- Forbidden API: placement, recall, policy, storage, trace, or audit implementation.
- Dependencies: references module packages only for composition.
- Failure: packaging can fail; installed Core correctness is unchanged.
- Distributions: owns all five named assembly manifests.
- Future repository: `nollm-distributions`.
- Current sources: root packaging/delivery metadata and future distribution manifests.
