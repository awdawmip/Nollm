# GRF8 Memory Quality

The first deterministic benchmark contains six categories, 10,000 evidence
items, and 1,000 ground-truth queries. Metrics are computed from rankings:
Precision@K, Recall@K, MRR, nDCG, source faithfulness, revision correctness,
and false relation rate. Results are limited to this fixture.

On the fixed 1,000-query run, N3-N5 produced MRR/nDCG/Recall@5 of `0.933`
with false relation rate `0.0`. The lexical, vector-like, and graph baselines
were separately ranked on the same corpus and scored lower. These values do
not claim generalization beyond this deterministic fixture.
