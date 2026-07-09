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

```text
GATE_G_PASSED
- append-only ledger implemented;
- every durable GRF object write has ledger event when recorded_at is supplied;
- object hash matches canonical bytes;
- different-byte rewrite rejected without overwrite;
- relation field rebuilt from files;
- replayed recall matches in-memory recall on selected_shards and path classes;
- rejected stitch records reload and suppress repeated false-friend acceptance;
- RecallDigest is derived and source objects remain authoritative.
```

## Gate H

Pending implementation.
