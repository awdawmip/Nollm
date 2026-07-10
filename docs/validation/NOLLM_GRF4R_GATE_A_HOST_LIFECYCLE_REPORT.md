# NOLLM GRF4R Gate A Host Lifecycle Report

GATE_A_PASS.

FileHost, OpenClawLikeHost, and CodexLikeHost fixtures each execute session
creation, capability negotiation, capture, simulated interrupted delivery,
retry, duplicate capture, place, admit, recall, replay, validation, and invalid
capability rejection. Every operation reaches Core through an adapter and the
versioned Host Contract.

All hosts receive the same Core-created evidence identity for the same capture
input. Duplicate and retry capture leave `evidence_shard_count = 1`. Recall and
replay results are byte-equivalent mappings. Host fixtures own only request and
session state; they neither construct GRF identities nor access Core stores.
