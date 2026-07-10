# GRF7R3 Compact Evidence Handoff

## Scope

GRF7R3 changes only evidence delivery. It does not change GRF7R2 production
semantics, the durable host registry, negative-query execution, or sustained
mutation workload.

## Verification Modes

Local Full Mode verifies the complete Windows-local evidence pack byte for
byte, its manifest Merkle root, and the delivery receipt. External Compact Mode
verifies the Git bundle, receipt, manifest, deterministic raw-evidence samples,
reports, and transcripts contained in the compact audit capsule.

Full raw evidence was verified locally on Windows. External review received a
compact audit capsule, not the complete raw evidence pack.

完整原始证据已在 Windows 本地验证；外部审计取得的是紧凑审计胶囊，
不是完整原始证据包。

Cross-platform portability was not validated in this stage.
