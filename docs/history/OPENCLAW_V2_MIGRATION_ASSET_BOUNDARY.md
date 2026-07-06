# OpenClaw V2 Migration Asset Boundary

OpenClaw material is preserved as a frozen migration asset for possible future
L5 Host Adapter or L6 Terminal work.

## Current Status

OpenClaw is not the current Nollm runtime path. It is not a Core dependency and
must not be imported by V2 L0-L3 source.

## Future Use

Future OpenClaw migration work must be explicitly authorized. It must classify
any adapter work as L5 and any terminal or product surface as L6. Both must pass
through L4 Host Contract and Execution Bridge.

## Prohibited Use

OpenClaw material must not be used to:

- bypass L4 host binding;
- make terminal message identity authoritative over Core evidence identity;
- introduce runtime activation in V2L0;
- introduce network, database, cache, LLM, NLP, embedding, semantic search, or
  global discovery dependencies into Core.
