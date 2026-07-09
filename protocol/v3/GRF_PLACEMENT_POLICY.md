# GRF Placement Policy

`grf_deterministic_policy_v1` is a prototype deterministic placement policy.

It generates a bounded ordered set of candidates from:

- source-window seed
- island center
- patch boundary
- deterministic hash fallback
- density-relief alternative

Ranking uses Q16 integer arithmetic and stable tie-breaks. It does not use LLM,
NLP, embedding, global graph/vector search, semantic edge creation, topic
parents, network, database, or runtime daemon state.
