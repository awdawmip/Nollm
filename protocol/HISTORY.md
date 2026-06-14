# History

History is object-level ledger inspection.

Ledger is an audit trail, not memory recall. History reads that audit trail for one object, usually a card. Ledger/history do not prove truth, approve memory, change status, change trust, or perform semantic scoring.

Ledger/history are read-only unless an explicit write action such as `annotate`, `status`, or `nollm.update_status` is used.

Annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content.

History returns compact ledger event metadata and does not include card bodies by default.
