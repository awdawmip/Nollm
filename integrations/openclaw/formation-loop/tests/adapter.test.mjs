import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import plugin, { REVISION_CONFIRMATION_MAX_CALLS, REVISION_REDECISION_MAX_CALLS, asciiJson, batchAbsorptionModel, boundedTurns, extractAssistantText, extractResolvedModel, extractUserTurns, formationRetryable, latencyScenario, modelOverride, placementRetryable, registerDreamAgent, selectedRecallPaths, shouldApplyPlacement, surfaceBudget, traversalCorrectionPrompt, traversalRetryable, turnKey, wellFormedText } from "../dist/index.js";
import { CaptureStore } from "../dist/capture.js";

test("manifest exposes no main-agent Formation tool", () => {
  const manifest = JSON.parse(fs.readFileSync(new URL("../openclaw.plugin.json", import.meta.url)));
  assert.deepEqual(manifest.contracts.tools, []);
  assert.equal(manifest.configSchema.properties.prompt_version.default, "dream-json-p1");
  assert.equal(manifest.configSchema.properties.model_mode.default, "inherit");
  assert.equal(manifest.configSchema.properties.persist_subagent_transcripts.const, false);
  assert.equal(manifest.configSchema.properties.latency_validation_enabled.default, false);
  assert.equal(manifest.contracts.latencyCommitSchema, "nollm_memory_commit_latency_v1");
  assert.equal(manifest.contracts.latencyRecallSchema, "nollm_memory_recall_latency_v1");
  assert.equal(manifest.configSchema.properties.geometry_profile.const, "default_dream_v1");
  assert.equal(manifest.configSchema.properties.geometry_contract_version.const, "nollm_bounded_approximate_hex_coverage_v1");
  assert.equal(manifest.configSchema.properties.coordinate_domain_version.const, "nollm_hex_radius_2p31_default_chart_null_phase_v1");
  assert.equal(manifest.configSchema.properties.coverage_policy_version.const, manifest.contracts.coveragePolicyVersion);
  assert.equal(manifest.configSchema.properties.writable_field_contract_version.const, manifest.contracts.writableFieldContractVersion);
  assert.equal(manifest.configSchema.properties.storage_hex_radius.const, manifest.contracts.storageHexRadius);
  assert.equal(manifest.configSchema.properties.active_writable_hex_radius.const, manifest.contracts.activeWritableHexRadius);
  assert.equal(manifest.configSchema.properties.max_coverage_down_steps.const, manifest.contracts.maxCoverageDownSteps);
  assert.equal(manifest.configSchema.properties.physical_residual_schema_version.const, "nollm_bounded_approximate_coverage_residual_v1");
  assert.equal(manifest.contracts.physicalEntryWire, "nollm_openclaw_single_physical_entry_recall_v1");
  assert.equal(manifest.contracts.surfaceWire, "nollm_openclaw_bounded_approximate_surface_traversal_v1");
  assert.equal(manifest.configSchema.properties.surface_wire_version.const, manifest.contracts.surfaceWire);
  assert.equal(manifest.configSchema.properties.active_semantic_write_policy_version.const, manifest.contracts.activeSemanticWritePolicyVersion);
  assert.equal(manifest.configSchema.properties.surface_legal_actions_contract_version.const, manifest.contracts.surfaceLegalActionsContractVersion);
  assert.equal(manifest.configSchema.properties.physical_entry_resolution_policy_version.const, manifest.contracts.physicalEntryResolutionPolicyVersion);
  assert.equal(manifest.configSchema.properties.traversal_correction_max_attempts.const, manifest.contracts.traversalCorrectionMaxAttempts);
  assert.equal(manifest.version, "0.14.0");
  assert.equal(manifest.configSchema.properties.dream_sculptor_schema_version.const, manifest.contracts.dreamSculptorWire);
  assert.equal(manifest.configSchema.properties.locality_atlas_candidate_limit.maximum, 64);
  assert.equal(manifest.contracts.dreamSculptorCommonProviderCalls, 1);
  assert.equal(manifest.contracts.recallLensesPersistent, false);
  assert.equal(manifest.contracts.maxRecallLensesPerStatement, 4);
  assert.equal(manifest.contracts.junctionCandidateLimit, 8);
  assert.equal(manifest.configSchema.properties.revision_confirmation_schema_version.const, manifest.contracts.revisionConfirmationWire);
  assert.equal(manifest.configSchema.properties.revision_confirmation_max_calls.const, 1);
  assert.equal(manifest.configSchema.properties.revision_redecision_max_calls.const, 1);
  assert.equal(manifest.configSchema.properties.revision_confirmation_model_mode.const, "inherit");
  assert.equal(manifest.configSchema.properties.surface_page_size.maximum, 8);
  assert.equal(manifest.configSchema.properties.surface_max_order.maximum, 8);
  assert.equal(manifest.configSchema.properties.recall_surface_max_calls.default, 24);
  assert.equal(manifest.configSchema.properties.placement_surface_max_calls.default, 32);
  assert.equal(JSON.stringify(manifest.configSchema).includes("cursor"), false);
});

test("Surface budgets are fixed structural values with bounded calls", () => {
  const recall = surfaceBudget({}, "recall");
  const placement = surfaceBudget({}, "placement");
  assert.deepEqual(Object.keys(recall), Object.keys(placement));
  assert.equal(recall.page_size, 8);
  assert.equal(recall.max_calls, 24);
  assert.equal(placement.max_calls, 32);
  assert.equal(recall.hard_max_order, 8);
  assert.equal("selected_entries_limit" in recall, false);
  assert.equal("query" in recall, false);
  assert.equal("session" in recall, false);
});

test("selected Recall paths remain observational and statement-bound", () => {
  const paths = selectedRecallPaths([
    { statement_id: "entry", path: [], path_is_not_truth_proof: true },
    { statement_id: "target", path: ["coverage_down"], path_is_not_truth_proof: true },
  ], ["target"]);
  assert.deepEqual(paths, [{ statement_id: "target", path: ["coverage_down"], path_is_not_truth_proof: true }]);
  assert.deepEqual(selectedRecallPaths({}, ["target"]), []);
});

test("wire text replaces isolated UTF-16 surrogates before UTF-8 encoding", () => {
  assert.equal(wellFormedText("valid \udc94 text"), "valid \ufffd text");
});

test("Python bridge wire is ASCII-safe and lossless for Windows pipes", () => {
  const value = { text: "项目周会 📅 每周二上午九点" };
  const wire = asciiJson(value);
  assert.equal(/[^\x00-\x7f]/.test(wire), false);
  assert.deepEqual(JSON.parse(wire), value);
});

test("plugin registers channel delivery, recall preparation, and Gateway completion hooks with no tool", () => {
  const hooks = new Map(); let toolCount = 0;
  registerDreamAgent({ pluginConfig: { enabled: false }, on(name, handler) { hooks.set(name, handler); }, registerTool() { toolCount += 1; } });
  assert.deepEqual([...hooks.keys()].sort(), ["agent_end", "agent_turn_prepare", "before_agent_run", "llm_output", "message_received", "message_sent", "subagent_ended", "subagent_spawned"]);
  assert.equal(toolCount, 0);
});

test("recall NONE paths emit explicit audit evidence", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.match(source, /built\.status === "complete_none"/);
  assert.match(source, /rendered\.outcome === "none"/);
  assert.equal((source.match(/status: "completed_none", stage: "recall"/g) ?? []).length, 2);
  assert.match(source, /stage: "recall_surface_terminal"/);
  for (const field of ["surface_build_ms", "surface_order_count", "surface_projection_count", "surface_page_count", "physical_entry_resolution_ms", "recall_core_ms", "recall_agent_ms", "total_operation_ms"]) {
    assert.equal(source.includes(field), true);
  }
});

test("placement evidence carries the bounded Surface traversal path", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.match(source, /stage: "placement_apply"[^\n]+surface_path: surfacePath/);
  assert.match(source, /\.\.\.applied, operation_timing: timing/);
  assert.match(source, /surfacePath\.push\(built\.surface \?\? built\.physical_entries\)/);
  assert.equal((source.match(/built\.status === "traverse" \|\| built\.status === "physical_entry"/g) ?? []).length, 2);
  for (const field of ["formation_ms", "surface_build_ms", "placement_subagent_ms", "physical_entry_resolution_ms", "placement_apply_ms", "handle_bind_ms", "total_operation_ms", "timeout_stage"]) {
    assert.equal(source.includes(field), true);
  }
});

test("ConversationMaterial uses real role messages and excludes system content", () => {
  const messages = [
    { role: "system", content: "hidden bootstrap" },
    { role: "user", content: "first\nuser" },
    { role: "assistant", content: [{ type: "text", text: "prior answer" }] },
    { role: "user", content: [{ type: "text", text: "current user" }] },
    { role: "assistant", content: "current answer" },
  ];
  assert.deepEqual(extractUserTurns(messages).map(x => x.content_utf8), ["first\nuser", "current user"]);
  assert.equal(extractAssistantText(messages), "current answer");
  const bounded = boundedTurns(extractUserTurns(messages), extractAssistantText(messages), 1000);
  assert.deepEqual(bounded.map(x => x.role), ["user", "user", "assistant"]);
  assert.equal(JSON.stringify(bounded).includes("hidden bootstrap"), false);
});

test("TurnKey prefers run identity and is stable across hooks", () => {
  assert.equal(turnKey("s", "run-1", "inbound", "one"), turnKey("s", "run-1", "outbound", "two"));
  assert.notEqual(turnKey("s", "run-1"), turnKey("s", "run-2"));
});

test("latency scenario labels come only from bounded validation session tags", () => {
  assert.equal(latencyScenario({}, "agent:main:aold-latency-W_NEW_MULTI-01"), "W_NEW_MULTI");
  assert.equal(latencyScenario({}, "agent:main:aold-latency-R_DENSE_HIDDEN_PREVIEW-02"), "R_DENSE_HIDDEN_PREVIEW");
  assert.equal(latencyScenario({}, "agent:main:aold-latency-PREHEAT-01"), "PREHEAT");
  assert.equal(latencyScenario({}, "agent:main:explicit:aold-latency-r_none-01"), "R_NONE");
  assert.equal(latencyScenario({ latency_scenario_id: "configured" }, "ordinary-session"), "configured");
  assert.equal(latencyScenario({}, "W_INVENTED"), "unspecified");
});

test("canonical model refs project to Host provider and model fields", () => {
  assert.deepEqual(modelOverride("meituan/LongCat-2.0"), { provider: "meituan", model: "LongCat-2.0" });
  assert.equal(modelOverride("missing-provider"), undefined);
});

test("batch absorption uses one explicit allowed model when delivery metadata is absent", () => {
  assert.equal(batchAbsorptionModel({ model_mode: "inherit", allowed_models: ["meituan/LongCat-2.0"] }, [{ model_ref: undefined }]), "meituan/LongCat-2.0");
  assert.equal(batchAbsorptionModel({ model_mode: "inherit", allowed_models: ["one/model", "two/model"] }, [{ model_ref: undefined }]), undefined);
  assert.equal(batchAbsorptionModel({ model_mode: "inherit", allowed_models: ["one/model"] }, [{ model_ref: "observed/model" }]), "observed/model");
});

test("resolved child model comes from the final assistant session message", () => {
  const messages = [
    { role: "assistant", provider: "old", model: "old-model", content: "first" },
    { role: "user", content: "next" },
    { role: "assistant", provider: "meituan", model: "LongCat-2.0", content: "final" },
  ];
  assert.deepEqual(extractResolvedModel(messages), {
    resolved_provider: "meituan",
    resolved_model: "LongCat-2.0",
    resolved_model_ref: "meituan/LongCat-2.0",
  });
  assert.deepEqual(extractResolvedModel([{ role: "assistant", content: "missing metadata" }]), {});
});

test("delivery hooks await only local Capture and do not call runtime inline", async () => {
  const hooks = new Map(); let spawnCount = 0;
  registerDreamAgent({ pluginConfig: {}, on(name, handler) { hooks.set(name, handler); }, runtime: { subagent: { run() { spawnCount += 1; } } } });
  hooks.get("message_received")({ content: "real user", runId: "r" }, { sessionKey: "s", runId: "r" });
  await hooks.get("message_sent")({ success: true, content: "reply", runId: "r" }, { sessionKey: "s", runId: "r" });
  await hooks.get("agent_end")({ success: true, runId: "r", messages: [{ role: "user", content: "real user" }, { role: "assistant", content: "reply" }] }, { sessionKey: "s", runId: "r", messageProvider: "webchat" });
  assert.equal(spawnCount, 0);
});

test("delivery Capture is durable before return and pending fallback crosses sessions without Provider", async () => {
  const root = fs.mkdtempSync(join(tmpdir(), "nollm-hook-capture-"));
  try {
    const hooks = new Map(); let spawnCount = 0;
    registerDreamAgent({
      pluginConfig: { capture_workspace: root, capture_enabled: true, absorption_enabled: false, capture_scope_id: "fallback" },
      on(name, handler) { hooks.set(name, handler); },
      runtime: { subagent: { run() { spawnCount += 1; } } },
    });
    hooks.get("message_received")({ content: " exact user\n", runId: "r" }, { sessionKey: "session-one", runId: "r", userId: "u1" });
    await hooks.get("message_sent")({ success: true, content: "exact assistant\n", runId: "r" }, { sessionKey: "session-one", runId: "r", userId: "u1" });
    const records = await new CaptureStore(root).allRecords();
    assert.equal(records.length, 1);
    assert.equal(records[0].user_utf8, " exact user\n");
    assert.equal(records[0].assistant_utf8, "exact assistant\n");
    const prepared = await hooks.get("agent_turn_prepare")({ prompt: "what did I say?" }, { sessionKey: "session-two", runId: "q", userId: "u1" });
    assert.match(prepared.appendContext, /exact user/);
    assert.equal(spawnCount, 0);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test("missing host configuration fails open after delivery", async () => {
  const hooks = new Map(); let spawnCount = 0;
  registerDreamAgent({ pluginConfig: {}, on(name, handler) { hooks.set(name, handler); }, runtime: { subagent: { async run() { spawnCount += 1; return { runId: "bad" }; } } } });
  hooks.get("message_received")({ content: "A durable user preference." }, { sessionKey: "s" });
  hooks.get("llm_output")({ provider: "p", model: "m" }, { sessionKey: "s" });
  await hooks.get("message_sent")({ success: true, content: "Normal visible reply." }, { sessionKey: "s" });
  assert.equal(spawnCount, 0);
});

test("failed delivery and disallowed model never spawn Dream", async () => {
  const hooks = new Map(); let spawnCount = 0;
  registerDreamAgent({ pluginConfig: { python_executable: "python", nollm_repo_root: ".", allowed_models: ["allowed/model"] }, on(name, handler) { hooks.set(name, handler); }, runtime: { subagent: { async run() { spawnCount += 1; return { runId: "bad" }; } } } });
  hooks.get("message_received")({ content: "Durable material." }, { sessionKey: "s" });
  hooks.get("llm_output")({ provider: "other", model: "model" }, { sessionKey: "s" });
  await hooks.get("message_sent")({ success: false, content: "not delivered" }, { sessionKey: "s" });
  await hooks.get("message_sent")({ success: true, content: "delivered" }, { sessionKey: "s" });
  hooks.get("agent_end")({ success: true, runId: "channel-run", messages: [] }, { sessionKey: "s", messageProvider: "telegram" });
  assert.equal(spawnCount, 0);
});

test("shadow Formation never continues into Placement", () => {
  const parsed = { ok: true, statements: [{ statement_id: "s" }] };
  assert.equal(shouldApplyPlacement({ write_mode: "shadow", statement_store_workspace: "C:\\temp" }, parsed, "meituan/LongCat-2.0"), false);
  assert.equal(shouldApplyPlacement({ write_mode: "statement-store", statement_store_workspace: "C:\\temp" }, parsed, "meituan/LongCat-2.0"), true);
});

test("engineering input errors never trigger a Formation model retry", () => {
  assert.equal(formationRetryable({ ok: false, error: "invalid_input" }), false);
  assert.equal(formationRetryable({ ok: false, error: "bridge_process_error" }), false);
  assert.equal(formationRetryable({ ok: false, error: "invalid_json" }), true);
  assert.equal(formationRetryable({ ok: false, error: "invalid_schema" }), true);
});

test("Placement retries only JSON and schema failures", () => {
  assert.equal(placementRetryable({ ok: false, error: "invalid_json" }), true);
  assert.equal(placementRetryable({ ok: false, error: "invalid_schema" }), true);
  assert.equal(placementRetryable({ ok: false, error: "invalid_input" }), false);
  assert.equal(placementRetryable({ ok: false, error: "bridge_process_error" }), false);
});

test("Traversal correction is bounded to recoverable model decisions", () => {
  assert.equal(traversalRetryable({ ok: false, error: "invalid_json" }), true);
  assert.equal(traversalRetryable({ ok: false, error: "invalid_surface_traversal" }), true);
  assert.equal(traversalRetryable({ ok: false, error: "bridge_process_error" }), false);
  const prompt = traversalCorrectionPrompt("Allowed responses:\n{\"action\":\"none\"}", "bad", { error: "invalid_surface_traversal", message: "not legal" }, 1);
  assert.match(prompt, /Correction attempt 1 of 2/);
  assert.match(prompt, /Allowed responses/);
  assert.match(prompt, /without changing traversal or memory state/);
});

test("Traversal evidence distinguishes correction, singleton skip, and provider timeout", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  for (const field of ["model_call_count", "invalid_decision_count", "correction_attempt_count", "correction_success", "provider_timeout_stage", "physical_entry_model_call_skipped"]) {
    assert.equal(source.includes(field), true);
  }
  assert.match(source, /correction_attempt_count\) >= TRAVERSAL_CORRECTION_MAX_ATTEMPTS/);
});

test("destructive revision uses one confirmation and at most one redecision", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.equal(REVISION_CONFIRMATION_MAX_CALLS, 1);
  assert.equal(REVISION_REDECISION_MAX_CALLS, 1);
  assert.match(source, /applied\.outcome === "revision_confirmation_required"/);
  assert.match(source, /action: "build_revision_confirmation_prompt"/);
  assert.match(source, /confirmation\.outcome === "confirm_revision"/);
  assert.match(source, /confirmation\.outcome === "reject_revision"/);
  assert.match(source, /action: "build_revision_redecision_prompt"/);
  assert.match(source, /revision_confirmation_call_consumed/);
  for (const field of ["revision_confirmation_count", "revision_confirmation_ms", "revision_confirmation_outcome", "revision_redecision_count", "revision_redecision_ms", "revision_target_blacklisted"]) {
    assert.equal(source.includes(field), true);
  }
});

test("a run satisfied by hidden Recall cannot re-form the recalled fact", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.match(source, /type Candidate[\s\S]+const recallSatisfiedSessions = new Set<string>\(\);[\s\S]+export function registerDreamAgent/);
  assert.match(source, /recallSatisfiedSessions\.add\(ctx\.sessionKey\)/);
  assert.match(source, /api\.on\("agent_turn_prepare"[\s\S]+recallSatisfiedSessions\.delete\(ctx\.sessionKey\)/);
  assert.match(source, /recallSatisfiedSessions\.has\(sessionKey\)/);
  assert.match(source, /reason: "same_run_satisfied_by_recall"/);
});

test("Recall-to-visible pending correlation is process-wide but memory-only", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.match(source, /const pendingRecallLatencyByRun = new Map<string, PendingRecallLatency>\(\)/);
  assert.match(source, /correlation_failure: "message_sent_not_observed"/);
  assert.equal(source.includes("pendingRecallLatencyByRun.json"), false);
});

test("plugin entry is an ordinary hook plugin", () => {
  assert.equal(plugin.id, "nollm-formation");
  assert.equal(typeof plugin.register, "function");
});

test("background absorption uses one Dream Sculptor call and per-Capture outcomes", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  const start = source.indexOf("const absorbCapturedBatch");
  const end = source.indexOf("const absorptionWorker", start);
  const body = source.slice(start, end);
  assert.match(body, /action: "build_dream_sculptor_prompt"/);
  assert.match(body, /action: "apply_dream_sculptor_result"/);
  assert.equal(body.includes('action: "build_batch_placement_prompt"'), false);
  assert.equal(body.includes(":placement`"), false);
  assert.match(body, /source_capture_ids\.includes\(record\.capture_id\)/);
  assert.match(body, /common_one_call: providerCalls === 1/);
  assert.match(body, /const providerKey = `\$\{batchId\}:\$\{executionId\}`/);
  assert.match(body, /Dream Sculptor failed: \$\{sculptorRun\.error/);
  assert.match(body, /stage: "dream_sculptor_validation"/);
  assert.match(body, /validated_plans: applied\.plans, durable_outcomes: outcomes/);
});

test("background absorption timer follows the Host service lifecycle", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.match(source, /id: "nollm-durable-capture-absorption"/);
  assert.match(source, /start: \(\) => \{ absorptionServiceRunning = true; scheduleAbsorption\(\); \}/);
  assert.match(source, /stop: \(\) => \{/);
  assert.match(source, /if \(absorptionTimer\) clearTimeout\(absorptionTimer\)/);
  assert.match(source, /if \(!absorptionServiceRunning\) return/);
});
