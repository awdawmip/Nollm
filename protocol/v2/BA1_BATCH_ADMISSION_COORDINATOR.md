# BA1 Batch Admission Coordinator

BA1 coordinates host-explicit deferred candidate selections into independent
DA1 admission requests. It does not choose candidates, generate promotion
decisions, generate growth submissions, generate placement plans, assemble a
field, or execute recall.

## Objects

- `PromotionDecision`: host-provided decision for one candidate. BA1 accepts
  only `decision=promote` and `next_action=request_growth_submission`.
- `BatchAdmissionWindow`: transient coordination boundary. It is not a queue,
  folder, parent node, source of truth, Field, or recall object.
- `BatchAdmissionMember`: one candidate id, one promotion decision, and one
  complete host-built DA1 `AdmissionRequest`.
- `BatchAdmissionRequest`: one window, non-empty members, and host-provided
  `submitted_at`.
- `BatchAdmissionReceipt`: narrow, in-memory result containing member identity
  and DA1 `AdmissionReceipt` values only.

## Flow

```text
explicit candidate IDs
+ explicit PromotionDecision values
+ explicit DA1 AdmissionRequest values
        |
        v
BA1 all-member zero-write preflight
        |
        v
serial independent DA1 admit calls
        |
        v
independent AdmissionRecords + narrow batch receipt
```

## Preflight

BA1 first validates the whole batch before any DA1 commit:

- window is `ready_for_selection` and not closed;
- shared geometry profile matches DA1 `FIELD_PROFILE_ID`;
- member, candidate, promotion decision, admission, placement plan, and shard
  identities are unique;
- each candidate is read only by explicit `candidate_id`;
- each candidate's shard is read from DE1 by explicit `candidate.shard_id`;
- each decision matches the candidate and shard;
- each host DA1 request contains the exact DE1 DreamShard;
- `window.member_shard_ids` equals the actual member shard set;
- DA1 `preflight(...)` accepts every sanitized request;
- compiled proposal identities returned by DA1 preflight are unique across the
  batch.

Any preflight failure rejects the batch before any DA1 `admit(...)` call. BA1
normalizes structured lower-layer preflight failures into `BA1Rejection` with
`BA1_MEMBER_PREFLIGHT_REJECTED` while preserving structured reason codes when
the lower layer exposes them.

## Commit

After all members preflight successfully, BA1 calls DA1 serially in canonical
`member_id` order. Each member remains an independent DA1 admission with its own
proposal, placement plan, AdmissionRecord, projection fingerprint, and receipt.

## Interruption And Retry

BA1 has no global transaction, rollback, crash recovery, queue, or background
retry. If commit is interrupted after one or more DA1 admissions complete, BA1
raises `BA1CommitInterrupted` with the completed member receipts and failed
member id. A later identical submit relies on DA1 idempotency for completed
members and continues unfinished members.

## Boundaries

BA1 does not mutate CI1 candidates, receipts, visibility, or policy. It does
not persist batch state. It does not read by global discovery or scan candidate
or admission stores. It does not call DF1, DR1, DI1, runtime, OpenClaw, CLI,
network, database, cache, LLM/NLP, embeddings, or semantic search.
