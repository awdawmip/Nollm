# NOLLM GRF3 Host Reconnection Architecture

```text
Host JSON -> File Adapter -> GRF Host Contract -> GRFHostService -> GRFFacade
                                                                  -> GRF Core
```

The dependency direction is one-way. The adapter imports the contract; the
Core contains no adapter, terminal, OpenClaw, Codex, or CLI imports. The
OpenClaw and Codex directories are declarative adapter skeletons only and do
not revive the retired legacy provider.

Identity namespaces remain separate at the contract boundary. A host request
does not become evidence, placement, or admission identity. Recall stays in
Core and returns its source fallback reference through the response unchanged.
