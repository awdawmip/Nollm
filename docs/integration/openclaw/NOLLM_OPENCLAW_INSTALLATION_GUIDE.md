# Installation Guide

Run from the repository root:

```powershell
pnpm --dir integrations/openclaw/grf-adapter install
pnpm --dir integrations/openclaw/grf-adapter build
powershell -ExecutionPolicy Bypass -File integrations/openclaw/grf-adapter/scripts/install.ps1
```

Verify with `openclaw plugins inspect nollm-grf --runtime --json`. Uninstalling the plugin only removes plugin assets; it does not delete GRF evidence.
