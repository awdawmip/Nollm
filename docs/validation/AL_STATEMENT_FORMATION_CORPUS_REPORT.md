# AL Statement Formation Corpus Report

Corpus v1 contains 126 exact-span cases across 14 categories. It has 84
development and 42 held-out cases, with 42 Chinese, 42 English, and 42 mixed
language cases. Gold validation found zero invalid boundaries, overlap,
text mismatch, or unknown fields.

The perfect fixture achieves 1.0 for every applicable metric and zero
hallucinated text. The off-by-one fixture is accepted as evidence-faithful but
scores below exact Gold span metrics. Unknown evidence, overlap, duplicate
identity, noncanonical order, rewritten or invented fields, empty formed state,
defer conflict, and forbidden field injection are rejected.

This is contract and Gold Corpus validation. No actual LLM was run. The results
do not establish model formation quality, geometric placement, recall quality,
or product effectiveness.
