# Statement Formation Corpus v1

This directory validates an evidence-preserving exact-span contract. Gold
boundaries are supplied by fixtures; the Python tools validate and score them
without deriving semantic boundaries.

- `development` cases are available for future tool development.
- `held_out` cases preserve an evaluation boundary. Future tuning tools must
  not consume their Gold decisions.
- Unicode offsets are Python string indices, which count Unicode code points.
  They are not UTF-8 byte offsets and do not model grapheme clusters.
- Reports validate contracts and fixtures only. They do not report model,
  placement, recall, or product quality.
