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
  STUB_NONZERO_ACTIVE_ERROR,
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
      { agentId: "main", sessionId: "s1", runId: "run-1" }
    );
    assert.ok(result.prependContext.includes("NOLLM_MEMORY_CONTEXT_V1"));
    assert.ok(result.prependContext.includes("freshness: fresh"));
    assert.ok(result.prependContext.includes("stub claim about Nollm"));
  });

  it("uses event.prompt when prepare messages do not include a user turn", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const payloadPath = path.join(tmp, "prepare-payload.json");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys",
      "stdin = json.loads(sys.stdin.read())",
      "open(r'" + payloadPath.replace(/\\/g, "\\\\") + "', 'w', encoding='utf-8').write(json.dumps(stdin, ensure_ascii=False, sort_keys=True))",
      "print(json.dumps({",
      "  'ok': True,",
      "  'schema': 'nollm.provider.prepare.v2',",
      "  'context': {'schema': 'NOLLM_MEMORY_CONTEXT_V1', 'freshness': 'none', 'facts': [], 'boundaries': [], 'warnings': [], 'explicit_absences': []},",
      "  'metrics': {'native_record_count': 0, 'result_count': 0, 'rendered_context_characters': 80, 'recall_mode': 'none'}",
      "}, sort_keys=True))",
    ].join("\n"));
    const api = makeMockApi(cfg);
    createNollmProvider(api);
    await invokePrepare(
      api,
      { messages: [], prompt: "prompt fallback query" },
      { agentId: "main", sessionId: "s1", runId: "run-1" }
    );
    const payload = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    assert.equal(payload.query, "prompt fallback query");
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
    assert.ok(result.prependContext.includes("NOLLM_MEMORY_CONTEXT_V1"));
    assert.ok(result.prependContext.includes("freshness: none") || result.prependContext.includes("freshness: unavailable"));
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
    await invokeEnd(
      api,
      {
        runId: "run-1",
        success: true,
        messages: [{ role: "user", content: "hello" }],
      },
      { agentId: "main", sessionId: "s1", runId: "run-1" }
    );
    assert.equal(api._events.warnings.length, 0);
  });
});

describe("T8 sidecar stdin / shell:false / timeout / abort", () => {
  it("sends command and payload via stdin JSON", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_ECHO);
    const normalized = normalizeConfig(cfg);
    const result = await runSidecarCommand(normalized, "active-prepare", { query: "hello" });
    assert.equal(result.ok, true);
    assert.equal(result.command, "active-prepare");
    assert.ok(Array.isArray(result.argv));
    assert.ok(result.argv.includes("--native-store-root"));
    assert.ok(result.argv.includes("--trial-root"));
    assert.ok(result.native_store_root.includes("native-companion-v1"));
  });

  it("times out a slow sidecar", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp, { commandTimeoutMs: 1000 });
    writeStubSidecar(cfg.nollmRepoRoot, STUB_SLOW);
    const normalized = normalizeConfig(cfg);
    const start = Date.now();
    const result = await runSidecarCommand(normalized, "active-prepare", {});
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
    const promise = runSidecarCommand(normalized, "active-prepare", {}, controller.signal);
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
    const result = await runSidecarCommand(normalized, "active-prepare", {});
    assert.equal(result.ok, false);
    assert.equal(result.error.code, "sidecar_invalid_json");
  });

  it("preserves structured active error JSON from nonzero sidecar exits", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    writeStubSidecar(cfg.nollmRepoRoot, STUB_NONZERO_ACTIVE_ERROR);
    const normalized = normalizeConfig(cfg);
    const result = await runSidecarCommand(normalized, "active-prepare", {});
    assert.equal(result.ok, false);
    assert.equal(result.schema, "nollm.active_memory_error.v1");
    assert.equal(result.error.code, "native_recall_failed");
  });

  it("uses spawn with shell:false", () => {
    const source = fs.readFileSync(
      path.resolve(import.meta.dirname, "..", "dist", "sidecar.js"),
      "utf8"
    );
    assert.ok(source.includes("shell: false"), "sidecar spawn must set shell:false");
  });
});
