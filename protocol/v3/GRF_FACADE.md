# GRF Prototype Facade

`GRFFacade` is a prototype public surface for GRF validation.

Supported commands:

- capture
- admit
- recall
- replay
- validate

The facade only orchestrates GRF modules. It does not import HCG, HAG, HX, OCA,
OpenClaw, terminal runtime, network, database, embedding, or global graph/vector
search code.
