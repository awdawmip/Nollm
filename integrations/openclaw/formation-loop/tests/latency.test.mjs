import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { appendLatencyEvent, COMMIT_LATENCY_SCHEMA, durationMs, durationUs, RECALL_LATENCY_SCHEMA, sha256Text, turnCorrelationId } from "../dist/latency.js";

test("controlled monotonic clock yields exact nonnegative durations", () => {
  assert.equal(durationUs(1_000_000n, 1_234_567n), 234);
  assert.equal(durationMs(1_000_000n, 3_500_000n), 2.5);
  assert.throws(() => durationUs(2n, 1n), /moved backwards/);
});

test("correlation identities are deterministic and content-minimal", () => {
  assert.equal(sha256Text("same"), sha256Text("same"));
  assert.equal(turnCorrelationId("session", "run", "answer"), turnCorrelationId("session", "run", "answer"));
  assert.notEqual(turnCorrelationId("session", "run", "answer"), turnCorrelationId("session", "other", "answer"));
});

test("latency JSONL is disabled by default and emits versioned minimal records when enabled", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "nollm-latency-"));
  const evidence = path.join(root, "latency.jsonl");
  const clock = { epochMs: () => 1234, monotonicNs: () => 99n };
  await appendLatencyEvent({ latency_evidence_path: evidence }, COMMIT_LATENCY_SCHEMA, { event_type: "ignored" }, clock);
  await assert.rejects(fs.stat(evidence), /ENOENT/);
  const config = { latency_validation_enabled: true, latency_evidence_path: evidence, latency_scenario_id: "fake", latency_validation_run_id: "run-1" };
  await appendLatencyEvent(config, COMMIT_LATENCY_SCHEMA, { event_type: "commit", statement_id: "s1", duration_us: 10 }, clock);
  await appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { event_type: "recall", query_hash: sha256Text("private query"), duration_us: 20 }, clock);
  const records = (await fs.readFile(evidence, "utf8")).trim().split("\n").map(line => JSON.parse(line));
  assert.deepEqual(records.map(record => record.schema_version), [COMMIT_LATENCY_SCHEMA, RECALL_LATENCY_SCHEMA]);
  assert.deepEqual(records.map(record => record.event_epoch_ms), [1234, 1234]);
  assert.equal(JSON.stringify(records).includes("private query"), false);
  await fs.rm(root, { recursive: true, force: true });
});
