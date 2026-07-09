# GRF1-FH Validation Report

## Gate F

```text
GATE_F_PASSED
- GRF storage layout implemented;
- canonical JSON stable across roundtrip;
- all persisted objects have schema_version;
- ids determine paths and path traversal is rejected;
- duplicate same-byte write is idempotent;
- duplicate different-byte write is rejected;
- exact runtime objects preserve integers and do not serialize floats.
```

## Gate G

Pending implementation.

## Gate H

Pending implementation.
