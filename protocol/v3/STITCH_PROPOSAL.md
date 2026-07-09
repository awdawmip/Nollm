# GRF Stitch Proposal

GRF1-B stitching is an auditable bridge relation. It is not a truth merge and
not a parent-child relation.

```text
StitchWitness(type, strength_q16, refs, metadata)
StitchProposal(proposal_id, from_patch, to_patch, candidate_transform, witnesses, confidence_q16, state, expires_at=None)
StitchRecord(stitch_id, proposal_id, accepted_by, accepted_at, from_patch, to_patch, transform, residual_q16, bridge_kernel, evidence_refs, reversible=True)
BridgeKernel(bridge_id, from_patch, to_patch, weight_q16, bridge_class, max_steps, max_fanout, evidence_refs)
```

Strong witnesses:

```text
manual_bridge
source_backed_ref
reuse_observed
```

Medium witnesses:

```text
coverage_resonance
boundary_overlap
co_activation
```

Weak witnesses:

```text
lexical_hint
llm_semantic_suggestion
```

Weak witnesses alone cannot accept a StitchProposal. Accepted proposals must
have a strong witness, or a bounded multi-witness medium score with low
residual. Rejected proposals remain serializable as anti-stitch evidence.

BridgeKernel bounds:

```text
0 < weight_q16 <= Q16_ONE
max_steps >= 1
max_fanout >= 1
evidence_refs non-empty
```

Bridge kernels are separate relation objects. They do not contain merged shard
content, do not run global traversal, and do not mutate EvidenceIsland or
LocalPatch records.
