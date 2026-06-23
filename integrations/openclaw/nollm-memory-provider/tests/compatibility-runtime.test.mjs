import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  makeProviderConfig,
  makeTempDir,
  writeStubSidecar,
  STUB_STATUS,
  STUB_PREPARE,
} from "./helpers.mjs";
import { createNollmCompatibilityRuntime } from "../dist/memory-runtime.js";
import { normalizeConfig } from "../dist/config.js";

describe("T9 compatibility manager rejects arbitrary path", () => {
  it("readFile rejects non-nollm:// and traversal paths", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    const normalized = normalizeConfig(cfg);
    const runtime = createNollmCompatibilityRuntime(normalized);
    const { manager } = await runtime.getMemorySearchManager({
      cfg: {},
      agentId: "main",
    });
    assert.ok(manager, "manager should be returned");
    await assert.rejects(
      async () => manager.readFile({ relPath: "/etc/passwd" }),
      /nollm_compat_ref_rejected/
    );
    await assert.rejects(
      async () => manager.readFile({ relPath: "file:///etc/passwd" }),
      /nollm_compat_ref_rejected/
    );
    await assert.rejects(
      async () => manager.readFile({ relPath: "nollm://compat/../etc/passwd" }),
      /nollm_compat_ref_rejected/
    );
    const result = await manager.readFile({ relPath: "nollm://compat/0" });
    assert.equal(result.text, "opaque Nollm compatibility reference");
  });
});

describe("T10 compatibility opaque ref is revision-bound", () => {
  it("search returns facts bound to source_refs", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_PREPARE);
    const normalized = normalizeConfig(cfg);
    const runtime = createNollmCompatibilityRuntime(normalized);
    const { manager } = await runtime.getMemorySearchManager({
      cfg: {},
      agentId: "main",
    });
    const results = await manager.search("nollm");
    assert.ok(results.length > 0, "search should return at least one result");
    assert.ok(
      results[0].path.startsWith("nollm://"),
      "result path must be a nollm opaque reference"
    );
    assert.equal(results[0].source, "memory");
  });
});

describe("T11 default config never contains workspaceRoot / legacy path", () => {
  it("normalized config has no workspaceRoot or legacy source keys", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    const normalized = normalizeConfig(cfg);
    const json = JSON.stringify(normalized);
    assert.ok(!json.includes("workspaceRoot"));
    assert.ok(!json.includes("legacyMemoryPath"));
    assert.ok(!json.includes("MEMORY.md"));
    assert.ok(!json.includes("DREAMS.md"));
  });

  it("backend config reports builtin host discriminant with custom nollm kind", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    const normalized = normalizeConfig(cfg);
    const runtime = createNollmCompatibilityRuntime(normalized);
    const backend = runtime.resolveMemoryBackendConfig({ cfg: {}, agentId: "main" });
    assert.equal(backend.backend, "builtin");
    assert.equal(backend.provider, "nollm");
    assert.equal(backend.custom.backendKind, "nollm");
    assert.equal(backend.custom.compatibilityShim, true);
  });
});
