# NOLLM GRF5 Migration Report

`ContractVersionRegistry` is the authoritative Host contract version table.
`migrate_host_request` performs a deep-copy envelope migration from v1 to v2,
then validates the migrated request with `GRFHostRequest`.

No evidence, placement, admission, geometry, or fallback record is rewritten.
No durable store schema migration is required for this contract-only version
transition. Retired terminal and legacy provider paths remain outside the
migration registry and are not recoverable through it.
