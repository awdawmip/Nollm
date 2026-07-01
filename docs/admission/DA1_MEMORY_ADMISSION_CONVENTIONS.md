# DA1 Memory Admission Conventions

DA1 is a write orchestrator, not a reasoning layer.

- Hosts supply complete `DreamShard`, Growth submission, and placement plan
  values.
- DA1 does not infer content, axes, facts, charts, cells, coverage targets, or
  Field quality.
- Preflight must finish before any durable write.
- Durable writes happen in the fixed owner order: DE1, DC1, DA1.
- Partial failures are reported honestly. DA1 does not roll back valid DE1 or
  DC1 owner writes.
- Admission replay is read-only and compares deterministic fingerprints and ID
  sets.
- Public receipts expose only identifiers, counts, and projection fingerprint.
