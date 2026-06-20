# Durable Memory

- Nollm must treat OpenClaw `MEMORY.md` as a read-only source plane.
- OpenClaw Active Memory should act as the read-side Cortex entry point for Nollm.
- The current integration boundary is: memory-core owns durable memory files; Nollm Core owns dream shards and geometry.

