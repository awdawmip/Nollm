# Core Capability Validation Report

The read-only executable record is bound to:

```text
validated_code_commit = 7ff9690edeca71806bf5783787ef81367b9eb167
validated_code_tree_digest = b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27
validation_schema = nollm_core_capability_validation_v2
verified_capabilities = 25 / 25
```

The digest covers Core source/tests, Snapshot source, Trace source, the Lab
compile support, generator, parity runner, Minimal E2E, and the validator.
`--check` recomputes the digest and capabilities without writing the worktree.

Lab imports Core only through the package root public API. The public Core
allowlist was not expanded for Lab, and the generated artifact retains SHA-256
`21659434328e457e0d868ddc1dcbf64484739ffeb64eb61eb62197616ddf0eba`.

This is a capability record, not a sealed or final declaration.
