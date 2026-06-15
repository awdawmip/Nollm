# F0 Full Gate Runtime Triage

F0 hardens the internal local full gate without changing Nollm's stable recall,
audit, card, anchor, ledger, or tool surfaces.

The local gate checks package hygiene, the dream checks manifest, dream failure
triage, and optionally `python run_tests.py`. When pytest is included, a timeout
is reported as a failed component instead of being treated as a pass.

This remains an experimental runtime guard. It does not write cards, confirm
placements, create anchors, run geometry recall, add MCP behavior, or introduce
vector, graph, embedding, or external LLM dependencies.
