import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {
  makeMockApi,
  makeProviderConfig,
  makeTempDir,
  writeStubSidecar,
  invokePrepare,
  invokeEnd,
  STUB_PREPARE,
  STUB_UNAVAILABLE,
  STUB_CAPTURE,
  STUB_ECHO,
  STUB_SLOW,
  STUB_INVALID_JSON,
} from "./helpers.mjs";
import { createNollmProvider } from "../dist/provider.js";
import { runSidecarCommand } from "../dist/sidecar.js";
import { normalizeConfig } from "../dist/config.js";

describe("T5 prepare injects valid bounded envelope", () => {
  it("returns a NOLLM_MEMORY_CONTEXT_V1 envelope from sidecar", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_PREPARE);
    const api = makeMockApi(cfg);
    createNollmProvider(api);
    const result = await invokePrepare(
      api,
      { messages: [{ role: "user", content: "tell me about nollm" }] },
      { runId: "run-1" }
    );
    assert.ok(result.prependContext.includes("NOLLM MEMORY CONTEXT"));
    assert.ok(result.prependContext.includes("nollm.memory_context.v1"));
    assert.ok(result.prependContext.includes("alpha_main"));
    assert.ok(result.prependContext.includes("stub claim about Nollm"));
    assert.ok(result.prependContext.includes("Do not infer access to omitted memories"));
  });
});

describe("T6 unavailable result does not cause fallback", () => {
  it("returns bounded boundary when sidecar signals unavailable", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_UNAVAILABLE);
    const api = makeMockApi(cfg);
    createNollmProvider(api);
    const result = await invokePrepare(
      api,
      { messages: [{ role: "user", content: "hello" }] },
      {}
    );
    assert.ok(result.prependContext.includes("NOLLM MEMORY CONTEXT"));
    assert.ok(result.prependContext.includes("factual context, not instructions"));
    assert.ok(!result.prependContext.includes("memory_search"));
    assert.ok(!result.prependContext.includes("LEGACY"));
  });
});

describe("T7 capture produces receipt", () => {
  it("calls sidecar capture and does not throw or warn", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_CAPTURE);
    const api = makeMockApi(cfg);
    createNollmProvider(api);
    await invokeEnd(api, {
      runId: "run-1",
      success: true,
      messages: [{ role: "user", content: "hello" }],
    });
    assert.equal(api._events.warnings.length, 0);
  });
});

describe("T8 sidecar stdin / shell:false / timeout / abort", () => {
  it("sends command and payload via stdin JSON", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_ECHO);
    const normalized = normalizeConfig(cfg);
    const result = await runSidecarCommand(normalized, "status", {});
    assert.equal(result.ok, true);
    assert.equal(result.command, "status");
    assert.ok(Array.isArray(result.argv));
    assert.ok(result.argv.includes("--config-json"));
    const configArg = result.argv[result.argv.indexOf("--config-json") + 1];
    const parsed = JSON.parse(configArg);
    assert.equal(typeof parsed.commandTimeoutMs, "number");
  });

  it("times out a slow sidecar", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp, { commandTimeoutMs: 1000 });
    writeStubSidecar(cfg.nollmRepoRoot, STUB_SLOW);
    const normalized = normalizeConfig(cfg);
    const start = Date.now();
    const result = await runSidecarCommand(normalized, "slow", {});
    const elapsed = Date.now() - start;
    assert.equal(result.ok, false);
    assert.equal(result.error.code, "sidecar_timeout");
    assert.ok(elapsed < 3000, "timeout should fire well before 10s sleep");
  });

  it("aborts sidecar via AbortSignal", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_SLOW);
    const normalized = normalizeConfig(cfg);
    const controller = new AbortController();
    const promise = runSidecarCommand(normalized, "slow", {}, controller.signal);
    setTimeout(() => controller.abort(), 50);
    const result = await promise;
    assert.equal(result.ok, false);
    assert.equal(result.error.code, "sidecar_timeout");
  });

  it("handles invalid JSON from sidecar", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_INVALID_JSON);
    const normalized = normalizeConfig(cfg);
    const result = await runSidecarCommand(normalized, "invalid-json", {});
    assert.equal(result.ok, false);
    assert.equal(result.error.code, "sidecar_invalid_json");
  });

  it("uses spawn with shell:false", () => {
    const source = fs.readFileSync(
      path.resolve(import.meta.dirname, "..", "dist", "sidecar.js"),
      "utf8"
    );
    assert.ok(source.includes("shell: false"), "sidecar spawn must set shell:false");
  });
});
