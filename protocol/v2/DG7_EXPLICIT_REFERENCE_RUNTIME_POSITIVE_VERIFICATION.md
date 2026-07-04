# DG7 Explicit Reference Runtime Positive Verification

DG7 is a validation-only reference runtime path for a fixed, explicit, finite host scenario.

It runs existing public CI1, BA1, DA1, DF1, DG6, DR1, and DI1 interfaces in a local Python process and emits a canonical `RuntimePositiveVerificationReceipt`.

DG7 does not add a production runtime, OpenClaw integration, CLI surface, network service, automatic admission, semantic search, LLM/NLP extraction, persistent compaction, cache, database, global discovery, or performance claim.

The fixed scenario uses four explicit captures:

- A and B are captured, deferred, explicitly promoted through BA1, admitted through DA1, assembled by DF1, projected by DG6, and recalled through DR1/DI1.
- C is captured/deferred only and remains outside admission, assembly, projection, recall, and DI1 evidence.
- D is admitted through DA1 but excluded from the explicit DF1 finite set, so it remains outside the current snapshot, DG6 projection, DR1 recall, and DI1 envelope.

DG6 projection is a parallel view-only verification over the DF1 snapshot. It must not filter, rank, replace, or influence DR1/DI1 recall.

DG7-C1 requires the DF1 finite assembly set to be driven by `DG7ReferenceScenario.explicit_assembly_admission_ids`. The runner must compare BA1 observed admission IDs with the declared tuple using ordered tuple equality before DF1 assembly, and must reject any D-only, duplicate, missing, reordered, or invalid declaration without deriving a substitute set from BA1 output.

The DG7 receipt is derived runtime evidence. It is not memory content, not a global field, not a durable recall index, and not a source of truth.
