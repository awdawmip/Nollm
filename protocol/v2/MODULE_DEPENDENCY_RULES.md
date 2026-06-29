# V2 Module Dependency Rules

The only allowed production dependency direction is:

```text
protocol -> evidence, geometry, cortex
evidence + geometry -> field
protocol + evidence + geometry + field + cortex -> recall
protocol + evidence + cortex + recall -> adapters
validation -> any V2 module as read-only test support
```

Forbidden edges include:

- `geometry -> cortex`
- `geometry -> recall`
- `geometry -> adapters`
- `geometry -> OpenClaw`
- `field -> adapters`
- `field -> OpenClaw`
- `evidence -> geometry`
- `cortex -> field`
- `adapters -> geometry internals`
- V1/OpenClaw runtime -> V2 during DG0
- V2 -> V1 runtime/OpenClaw during DG0

The executable source of truth for these rules is `nollm.dream_geometry.protocol.dependency_rules`.
