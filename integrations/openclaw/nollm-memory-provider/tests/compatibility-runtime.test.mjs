import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  makeProviderConfig,
  makeTempDir,
  writeStubSidecar,
  STUB_STATUS,
} from "./helpers.mjs";
import { createNollmCompatibilityRuntime } from "../dist/memory-runtime.js";
import { normalizeConfig } from "../dist/config.js";

describe("T10 compatibility runtime is disabled in active W2 config", () => {
  it("getMemorySearchManager returns null manager", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    const normalized = normalizeConfig(cfg);
    const runtime = createNollmCompatibilityRuntime(normalized);
    const { manager, error } = await runtime.getMemorySearchManager({
      cfg: {},
      agentId: "main",
    });
    assert.equal(manager, null);
    assert.ok(error.includes("disabled"));
  });

  it("resolveMemoryBackendConfig reports active nollm mode", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    const normalized = normalizeConfig(cfg);
    const runtime = createNollmCompatibilityRuntime(normalized);
    const backend = runtime.resolveMemoryBackendConfig({ cfg: {}, agentId: "main" });
    assert.equal(backend.backend, "builtin");
    assert.equal(backend.provider, "nollm");
    assert.equal(backend.custom.backendKind, "nollm");
    assert.equal(backend.custom.compatibilityShim, false);
    assert.equal(backend.custom.activeMode, true);
  });
});
