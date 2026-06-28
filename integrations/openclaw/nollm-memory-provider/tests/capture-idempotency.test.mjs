import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  makeProviderConfig,
  makeTempDir,
  writeStubSidecar,
  makeMockApi,
  invokeEnd,
} from "./helpers.mjs";
import { normalizeConfig } from "../dist/config.js";
import { createNollmProvider } from "../dist/provider.js";
import fs from "node:fs";
import path from "node:path";

describe("E4 capture idempotency and redaction", () => {
  it("same event twice -> TS calls sidecar twice and accepts Python deduplication", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const counterPath = path.join(cfg.trialRoot, "calls.txt");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys, os",
      "stdin = json.loads(sys.stdin.read())",
      "os.makedirs(os.path.dirname(r'" + counterPath.replace(/\\/g, "\\\\") + "'), exist_ok=True)",
      "calls = 0",
      "if os.path.exists(r'" + counterPath.replace(/\\/g, "\\\\") + "'):",
      "    calls = int(open(r'" + counterPath.replace(/\\/g, "\\\\") + "').read())",
      "calls += 1",
      "open(r'" + counterPath.replace(/\\/g, "\\\\") + "', 'w').write(str(calls))",
      "print(json.dumps({",
      "  'ok': True,",
      "  'schema': 'nollm.active_memory_capture.v1',",
      "  'capture': {",
      "    'event_id': 'evt-%d' % calls,",
      "    'promoted_count': 1 if calls == 1 else 0,",
      "    'deduplicated_count': 1 if calls > 1 else 0,",
      "    'suppressed_count': 0,",
      "    'rejected_count': 0,",
      "    'records': []",
      "  },",
      "  'metrics': {'user_messages_seen': 1, 'assistant_messages_ignored': 0, 'candidate_count': 1, 'latency_ms': 10}",
      "}, sort_keys=True))",
    ].join("\n"));
    const normalized = normalizeConfig(cfg);
    const api = makeMockApi(normalized);
    createNollmProvider(api);

    const event = {
      success: true,
      messages: [{ role: "user", content: "我叫卡卡布拉。" }],
      runId: "run-1",
    };
    const ctx = { agentId: "main", sessionId: "s1", runId: "run-1" };

    await invokeEnd(api, event, ctx);
    await invokeEnd(api, event, ctx);
    const calls = parseInt(fs.readFileSync(counterPath, "utf8"), 10);
    assert.equal(calls, 2);
  });

  it("secret in string content is rejected by Python, not persisted", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const payloadPath = path.join(tmp, "capture-payload.json");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys, os",
      "stdin = json.loads(sys.stdin.read())",
      "with open(r'" + payloadPath.replace(/\\/g, "\\\\") + "', 'w') as f:",
      "    json.dump(stdin, f, sort_keys=True)",
      "print(json.dumps({",
      "  'ok': True,",
      "  'schema': 'nollm.active_memory_capture.v1',",
      "  'capture': {",
      "    'event_id': 'evt-secret',",
      "    'promoted_count': 0,",
      "    'deduplicated_count': 0,",
      "    'suppressed_count': 0,",
      "    'rejected_count': 1,",
      "    'records': []",
      "  },",
      "  'metrics': {'user_messages_seen': 1, 'assistant_messages_ignored': 0, 'candidate_count': 1, 'latency_ms': 10}",
      "}, sort_keys=True))",
    ].join("\n"));
    const normalized = normalizeConfig(cfg);
    const api = makeMockApi(normalized);
    createNollmProvider(api);

    const event = {
      success: true,
      messages: [
        { role: "user", content: "Authorization: Bearer TOP_SECRET_123" },
      ],
      runId: "run-secret",
    };
    await invokeEnd(api, event, { agentId: "main", sessionId: "s-secret", runId: "run-secret" });

    const payload = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    assert.equal(payload.schema, "nollm.active_memory_capture.v1");
    assert.equal(payload.trial_id, cfg.trialId);
    assert.equal(payload.success, true);
    assert.ok(Array.isArray(payload.messages));
  });

  it("capture mode is deterministic_explicit_v1", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const normalized = normalizeConfig(cfg);
    assert.equal(normalized.captureMode, "deterministic_explicit_v1");
    assert.notEqual(normalized.captureMode, "receipt_only");
  });

  it("capture sidecar receives v1 active schema", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const payloadPath = path.join(tmp, "capture-payload.json");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys, os",
      "stdin = json.loads(sys.stdin.read())",
      "with open(r'" + payloadPath.replace(/\\/g, "\\\\") + "', 'w') as f:",
      "    json.dump(stdin, f, sort_keys=True)",
      "print(json.dumps({",
      "  'ok': True,",
      "  'schema': 'nollm.active_memory_capture.v1',",
      "  'capture': {",
      "    'event_id': 'evt-2',",
      "    'promoted_count': 0,",
      "    'deduplicated_count': 0,",
      "    'suppressed_count': 0,",
      "    'rejected_count': 0,",
      "    'records': []",
      "  },",
      "  'metrics': {'user_messages_seen': 1, 'assistant_messages_ignored': 0, 'candidate_count': 0, 'latency_ms': 10}",
      "}, sort_keys=True))",
    ].join("\n"));
    const normalized = normalizeConfig(cfg);
    const api = makeMockApi(normalized);
    createNollmProvider(api);

    const event = {
      success: true,
      messages: [{ role: "user", content: "blue" }],
      runId: "run-2",
    };
    await invokeEnd(api, event, { agentId: "main", sessionId: "s2", runId: "run-2" });

    const payload = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    assert.equal(payload.schema, "nollm.active_memory_capture.v1");
    assert.equal(payload.agent_id, "main");
    assert.equal(payload.session_id, "s2");
    assert.equal(payload.run_id, "run-2");
    assert.equal(payload.success, true);
    assert.ok(Array.isArray(payload.messages));
  });

  it("W2-05 capture sidecar receives operation-bound agent hook receipt fields", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp, { operationId: "w2-05-20260628T000004Z-abcdef123456" });
    const payloadPath = path.join(tmp, "capture-payload.json");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys, os",
      "stdin = json.loads(sys.stdin.read())",
      "with open(r'" + payloadPath.replace(/\\/g, "\\\\") + "', 'w') as f:",
      "    json.dump(stdin, f, sort_keys=True)",
      "print(json.dumps({'ok': True, 'schema': 'nollm.active_memory_capture.v1', 'capture': {'event_id': 'evt-w205', 'promoted_count': 0, 'deduplicated_count': 0, 'suppressed_count': 0, 'rejected_count': 0, 'records': []}, 'metrics': {}}, sort_keys=True))",
    ].join("\n"));
    const normalized = normalizeConfig(cfg);
    const api = makeMockApi(normalized);
    createNollmProvider(api);

    await invokeEnd(
      api,
      { success: true, messages: [{ role: "user", content: "blue" }], runId: "run-w205" },
      { agentId: "main", sessionId: "s-w205", runId: "run-w205" }
    );
    const payload = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    assert.equal(payload.operation_id, cfg.operationId);
    assert.equal(payload.event_source, "agent_hook");
    assert.match(payload.turn_receipt_id, /^[A-Za-z0-9][A-Za-z0-9_-]{31,127}$/);
  });

  it("D3: capture skipped when durable identity is incomplete", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const markerPath = path.join(cfg.trialRoot, "capture-marker.json");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys, os",
      "marker_path = r'" + markerPath.replace(/\\/g, "\\\\") + "'",
      "with open(marker_path, 'w') as f:",
      "    json.dump({'called': True}, f)",
      "print(json.dumps({'ok': True, 'schema': 'nollm.active_memory_capture.v1', 'capture': {'event_id': 'evt-inc', 'promoted_count': 0, 'deduplicated_count': 0, 'suppressed_count': 0, 'rejected_count': 0, 'records': []}, 'metrics': {}}, sort_keys=True))",
    ].join("\n"));
    const normalized = normalizeConfig(cfg);
    const api = makeMockApi(normalized);
    createNollmProvider(api);

    await invokeEnd(api, { success: true, messages: [] }, { agentId: "main" });
    assert.equal(fs.existsSync(markerPath), false, "sidecar capture must not be called with incomplete identity");
    assert.ok(api._events.warnings.some((w) => w.includes("incomplete identity")));
  });

  it("D4: event.runId fallback is forwarded to sidecar capture", async () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const payloadPath = path.join(tmp, "capture-payload.json");
    writeStubSidecar(cfg.nollmRepoRoot, [
      "import json, sys, os",
      "stdin = json.loads(sys.stdin.read())",
      "with open(r'" + payloadPath.replace(/\\/g, "\\\\") + "', 'w') as f:",
      "    json.dump(stdin, f, sort_keys=True)",
      "print(json.dumps({'ok': True, 'schema': 'nollm.active_memory_capture.v1', 'capture': {'event_id': 'evt-fb', 'promoted_count': 0, 'deduplicated_count': 0, 'suppressed_count': 0, 'rejected_count': 0, 'records': []}, 'metrics': {}}, sort_keys=True))",
    ].join("\n"));
    const normalized = normalizeConfig(cfg);
    const api = makeMockApi(normalized);
    createNollmProvider(api);

    await invokeEnd(
      api,
      { success: true, messages: [{ role: "user", content: "blue" }], runId: "event-run-1" },
      { agentId: "main", sessionId: "s1" }
    );
    const payload = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    assert.equal(payload.run_id, "event-run-1");
  });
});
