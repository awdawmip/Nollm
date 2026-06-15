# D7 OpenClaw Dream Experiment

This is an offline fixture showing how OpenClaw-style output could be
represented as dream shards and placement candidates.

No runtime integration is provided here. There is no network call, no external
LLM call, no agent runtime, no automatic ontology generation, no automatic
anchor creation, and no production placement.

The fixture demonstrates:

- D3 `DreamShard` records for small utterance-like residues.
- D4 `DreamPlacementCandidate` records for explicit candidate geometry.
- Candidate status only; no confirmed memory and no card writing.
