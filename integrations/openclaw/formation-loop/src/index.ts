import { spawn } from "node:child_process";
import { appendFile, mkdir } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { AsyncResource } from "node:async_hooks";
import { dirname, join } from "node:path";
import { buildJsonPluginConfigSchema, definePluginEntry, type OpenClawPluginApi } from "openclaw/plugin-sdk/core";

export type RunResult = { code: number; stdout: string; stderr: string };
export type DreamConfig = {
  enabled?: boolean; python_executable?: string; nollm_repo_root?: string;
  statement_store_workspace?: string; write_mode?: "shadow" | "statement-store";
  memory_workspace?: string;
  geometry_profile?: "default_dream_v1"; geometry_contract_version?: "nollm_bounded_approximate_hex_coverage_v1";
  coordinate_domain_version?: "nollm_hex_radius_2p31_default_chart_null_phase_v1";
  coverage_policy_version?: "nollm_broad_residue_min_hit_1_v1";
  writable_field_contract_version?: "nollm_hex_storage_2p31_writable_2p30_depth2_v1";
  storage_hex_radius?: 2147483647; active_writable_hex_radius?: 1073741823; max_coverage_down_steps?: 2;
  physical_residual_schema_version?: "nollm_bounded_approximate_coverage_residual_v1";
  surface_wire_version?: "nollm_openclaw_bounded_approximate_surface_traversal_v1";
  active_semantic_write_policy_version?: "nollm_default_dream_layer0_safe_write_v1";
  surface_legal_actions_contract_version?: "nollm_access_state_derived_surface_legal_actions_v1";
  physical_entry_resolution_policy_version?: "mechanical_singleton_physical_entry_v1";
  traversal_correction_max_attempts?: 2;
  model_mode?: "inherit" | "dedicated"; model?: string; allowed_models?: string[];
  prompt_version?: string; timeout_ms?: number; max_material_chars?: number;
  max_statements?: number; max_statement_chars?: number; max_total_chars?: number;
  persist_subagent_transcripts?: boolean; debug_trace?: boolean; evidence_path?: string;
  surface_page_size?: number; surface_max_order?: number; surface_page_overhead_units?: number; surface_cell_preview_units?: number;
  recall_surface_max_pages?: number; recall_surface_max_cells?: number; recall_surface_max_projection_units?: number; recall_surface_max_calls?: number;
  placement_surface_max_pages?: number; placement_surface_max_cells?: number; placement_surface_max_projection_units?: number; placement_surface_max_calls?: number;
};

const JSON_SCHEMA = {
  type: "object", additionalProperties: false,
  properties: {
    enabled: { type: "boolean", default: true }, python_executable: { type: "string" }, nollm_repo_root: { type: "string" },
    statement_store_workspace: { type: "string" }, memory_workspace: { type: "string" }, write_mode: { type: "string", enum: ["shadow", "statement-store"], default: "shadow" },
    geometry_profile: { type: "string", const: "default_dream_v1", default: "default_dream_v1" }, geometry_contract_version: { type: "string", const: "nollm_bounded_approximate_hex_coverage_v1", default: "nollm_bounded_approximate_hex_coverage_v1" },
    coordinate_domain_version: { type: "string", const: "nollm_hex_radius_2p31_default_chart_null_phase_v1", default: "nollm_hex_radius_2p31_default_chart_null_phase_v1" },
    coverage_policy_version: { type: "string", const: "nollm_broad_residue_min_hit_1_v1", default: "nollm_broad_residue_min_hit_1_v1" },
    writable_field_contract_version: { type: "string", const: "nollm_hex_storage_2p31_writable_2p30_depth2_v1", default: "nollm_hex_storage_2p31_writable_2p30_depth2_v1" },
    storage_hex_radius: { type: "integer", const: 2147483647, default: 2147483647 },
    active_writable_hex_radius: { type: "integer", const: 1073741823, default: 1073741823 },
    max_coverage_down_steps: { type: "integer", const: 2, default: 2 },
    physical_residual_schema_version: { type: "string", const: "nollm_bounded_approximate_coverage_residual_v1", default: "nollm_bounded_approximate_coverage_residual_v1" },
    surface_wire_version: { type: "string", const: "nollm_openclaw_bounded_approximate_surface_traversal_v1", default: "nollm_openclaw_bounded_approximate_surface_traversal_v1" },
    active_semantic_write_policy_version: { type: "string", const: "nollm_default_dream_layer0_safe_write_v1", default: "nollm_default_dream_layer0_safe_write_v1" },
    surface_legal_actions_contract_version: { type: "string", const: "nollm_access_state_derived_surface_legal_actions_v1", default: "nollm_access_state_derived_surface_legal_actions_v1" },
    physical_entry_resolution_policy_version: { type: "string", const: "mechanical_singleton_physical_entry_v1", default: "mechanical_singleton_physical_entry_v1" },
    traversal_correction_max_attempts: { type: "integer", const: 2, default: 2 },
    model_mode: { type: "string", enum: ["inherit", "dedicated"], default: "inherit" }, model: { type: "string" },
    allowed_models: { type: "array", items: { type: "string" }, default: [] }, prompt_version: { type: "string", default: "dream-json-p1" },
    timeout_ms: { type: "integer", minimum: 1000, default: 120000 }, max_material_chars: { type: "integer", minimum: 1, default: 12000 },
    max_statements: { type: "integer", minimum: 1, default: 8 }, max_statement_chars: { type: "integer", minimum: 1, default: 4096 },
    max_total_chars: { type: "integer", minimum: 1, default: 8192 }, persist_subagent_transcripts: { type: "boolean", const: false, default: false },
    debug_trace: { type: "boolean", default: false }, evidence_path: { type: "string" },
    surface_page_size: { type: "integer", minimum: 1, maximum: 8, default: 8 }, surface_max_order: { type: "integer", minimum: 0, maximum: 8, default: 8 },
    surface_page_overhead_units: { type: "integer", minimum: 1, default: 8 }, surface_cell_preview_units: { type: "integer", minimum: 1, default: 4 },
    recall_surface_max_pages: { type: "integer", minimum: 1, default: 4 }, recall_surface_max_cells: { type: "integer", minimum: 1, default: 32 }, recall_surface_max_projection_units: { type: "integer", minimum: 1, default: 160 }, recall_surface_max_calls: { type: "integer", minimum: 1, default: 24 },
    placement_surface_max_pages: { type: "integer", minimum: 1, default: 6 }, placement_surface_max_cells: { type: "integer", minimum: 1, default: 48 }, placement_surface_max_projection_units: { type: "integer", minimum: 1, default: 240 }, placement_surface_max_calls: { type: "integer", minimum: 1, default: 32 },
  },
} as const;

export const TRAVERSAL_CORRECTION_MAX_ATTEMPTS = 2;

export function surfaceBudget(config: DreamConfig, mode: "recall" | "placement"): Record<string, number> {
  const recall = mode === "recall";
  return {
    page_size: config.surface_page_size ?? 8,
    max_pages: recall ? config.recall_surface_max_pages ?? 4 : config.placement_surface_max_pages ?? 6,
    max_surface_cells: recall ? config.recall_surface_max_cells ?? 32 : config.placement_surface_max_cells ?? 48,
    page_overhead_units: config.surface_page_overhead_units ?? 8,
    cell_preview_units: config.surface_cell_preview_units ?? 4,
    max_projection_units: recall ? config.recall_surface_max_projection_units ?? 160 : config.placement_surface_max_projection_units ?? 240,
    max_descent_depth: config.surface_max_order ?? 8,
    hard_max_order: config.surface_max_order ?? 8,
    max_calls: recall ? config.recall_surface_max_calls ?? 24 : config.placement_surface_max_calls ?? 32,
  };
}

export function selectedRecallPaths(candidates: unknown, selectedIds: unknown): Array<{ statement_id: string; path: string[]; path_is_not_truth_proof: true }> {
  if (!Array.isArray(candidates) || !Array.isArray(selectedIds) || selectedIds.some((value) => typeof value !== "string")) return [];
  const wanted = new Set(selectedIds as string[]);
  return candidates.flatMap((candidate) => {
    if (typeof candidate !== "object" || candidate === null) return [];
    const item = candidate as Record<string, unknown>;
    if (typeof item.statement_id !== "string" || !wanted.has(item.statement_id) || !Array.isArray(item.path) || item.path.some((value) => typeof value !== "string")) return [];
    return [{ statement_id: item.statement_id, path: item.path as string[], path_is_not_truth_proof: true as const }];
  });
}

export function run(command: string, args: string[], input?: string, timeoutMs = 120000, env?: NodeJS.ProcessEnv): Promise<RunResult> {
  return new Promise((resolve) => {
    const child = spawn(command, args, { windowsHide: true, stdio: "pipe", env });
    let stdout = ""; let stderr = ""; let settled = false;
    const finish = (value: RunResult) => { if (!settled) { settled = true; clearTimeout(timer); resolve(value); } };
    const timer = setTimeout(() => { child.kill(); finish({ code: -1, stdout, stderr: "timeout" }); }, timeoutMs);
    child.stdout.on("data", chunk => { stdout += chunk.toString("utf8"); });
    child.stderr.on("data", chunk => { stderr += chunk.toString("utf8"); });
    child.on("error", error => finish({ code: -1, stdout, stderr: error.message }));
    child.on("close", code => finish({ code: code ?? -1, stdout, stderr }));
    child.stdin.end(input);
  });
}

function pythonPath(config: DreamConfig): string {
  return ["packages/nollm-core/src", "packages/nollm-access/src", "integrations/openclaw/formation-loop/python"]
    .map(path => join(config.nollm_repo_root!, path)).join(";");
}

async function bridge(config: DreamConfig, envelope: object): Promise<Record<string, unknown>> {
  const wire = asciiJson(envelope);
  const framed = Buffer.from(wire, "utf8").toString("base64");
  const result = await run(config.python_executable!, ["-m", "nollm_openclaw_formation.bridge"], framed, config.timeout_ms, { ...process.env, NOLLM_BRIDGE_BASE64: "1", PYTHONUTF8: "1", PYTHONPATH: pythonPath(config) });
  if (result.code !== 0) return { ok: false, error: "bridge_process_error", detail: result.stderr };
  try { return JSON.parse(result.stdout); } catch { return { ok: false, error: "bridge_invalid_json", detail: result.stderr }; }
}

export type Turn = { role: "user" | "assistant"; content_utf8: string };
export type TriggerPhase = "AFTER_DELIVERY" | "AFTER_TURN";
type UserObservation = Turn & { identity: string };
type Pending = { users: UserObservation[]; resolvedModel?: string; runId?: string };
type Candidate = { sessionKey: string; runId?: string; assistant: string; phase: TriggerPhase; sourceHook: "message_sent" | "agent_end"; observedAt: number; users?: Turn[]; resolvedModel?: string };

export function wellFormedText(value: string): string {
  return Array.from(value, character => {
    const unit = character.charCodeAt(0);
    return character.length === 1 && unit >= 0xd800 && unit <= 0xdfff ? "\ufffd" : character;
  }).join("");
}

export function asciiJson(value: object): string {
  const json = JSON.stringify(value, (_key, item: unknown) => typeof item === "string" ? wellFormedText(item) : item);
  return json.replace(/[^\x00-\x7f]/g, character => `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`);
}

export function boundedTurns(users: Turn[], assistant: string, budget: number): Turn[] {
  const selected = [...users.slice(-2), { role: "assistant" as const, content_utf8: assistant }];
  let remaining = budget; const reversed: Turn[] = [];
  for (const turn of selected.reverse()) {
    if (remaining <= 0) break;
    const content = wellFormedText(turn.content_utf8.slice(0, remaining));
    if (content) reversed.push({ role: turn.role, content_utf8: content });
    remaining -= content.length;
  }
  return reversed.reverse();
}

export function extractAssistantText(messages: unknown[]): string | undefined {
  for (const item of [...messages].reverse()) {
    if (!item || typeof item !== "object") continue;
    const value = item as Record<string, unknown>;
    if (value.role !== "assistant") continue;
    if (typeof value.content === "string" && value.content.trim()) return value.content.trim();
    if (Array.isArray(value.content)) {
      const text = value.content.map(part => part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string" ? (part as Record<string, unknown>).text : "").join("").trim();
      if (text) return text;
    }
  }
  return undefined;
}

export function extractUserTurns(messages: unknown[]): Turn[] {
  return messages.flatMap(item => {
    if (!item || typeof item !== "object") return [];
    const value = item as Record<string, unknown>;
    if (value.role !== "user") return [];
    if (typeof value.content === "string" && value.content.trim()) return [{ role: "user" as const, content_utf8: value.content.trim() }];
    if (!Array.isArray(value.content)) return [];
    const content = value.content.map(part => part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string" ? (part as Record<string, unknown>).text : "").join("").trim();
    return content ? [{ role: "user" as const, content_utf8: content }] : [];
  }).slice(-2);
}

export function turnKey(sessionKey: string, runId?: string, messageId?: string, content = ""): string {
  const marker = runId || messageId || createHash("sha256").update(wellFormedText(content)).digest("hex");
  return `${sessionKey}\0${marker}`;
}

export function modelOverride(ref?: string): { provider: string; model: string } | undefined {
  if (!ref) return undefined;
  const separator = ref.indexOf("/");
  if (separator <= 0 || separator === ref.length - 1) return undefined;
  return { provider: ref.slice(0, separator), model: ref.slice(separator + 1) };
}

async function trace(config: DreamConfig, value: object): Promise<void> {
  if (!config.debug_trace || !config.evidence_path) return;
  await mkdir(dirname(config.evidence_path), { recursive: true });
  await appendFile(config.evidence_path, `${JSON.stringify(value)}\n`, "utf8");
}

export function registerDreamAgent(api: OpenClawPluginApi): void {
  const config = (api.pluginConfig ?? {}) as DreamConfig;
  const pending = new Map<string, Pending>();
  const inFlight = new Set<string>();
  const scheduled = new Set<string>();
  const childParents = new Map<string, { parentRunId?: string; requestedModel?: string }>();
  let duplicateHookObservationCount = 0;
  let duplicateDreamSuppressedCount = 0;
  const backgroundScope = new AsyncResource("nollm-formation-background");
  const queue = (work: () => void) => { queueMicrotask(() => backgroundScope.runInAsyncScope(work)); };
  const recordHandler = (hook: string, startedAt: number, extra: object) => {
    const returnedAt = Date.now();
    queue(() => { void trace(config, { status: "hook", hook, hook_observed_at: startedAt, hook_handler_returned_at: returnedAt, hook_handler_duration_ms: returnedAt - startedAt, ...extra }); });
  };
  const configuredModel = (resolved?: string): string | undefined => config.model_mode === "dedicated" ? config.model : resolved;
  const usableModel = (model?: string): boolean => Boolean(model) && (!config.allowed_models?.length || config.allowed_models.includes(model!));
  const runHiddenAgent = async (prompt: string, model: string, idempotencyKey: string): Promise<{ raw?: string; resolved: Record<string, string>; error?: string }> => {
    const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
    const override = config.model_mode === "dedicated" ? modelOverride(model) : undefined;
    try {
      const spawned = await api.runtime.subagent.run({ sessionKey: childSessionKey, message: prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey });
      const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
      if (waited.status !== "ok") return { error: waited.error ?? waited.status, resolved: {} };
      const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSessionKey, limit: 20 });
      return { raw: extractAssistantText(session.messages), resolved: extractResolvedModel(session.messages) };
    } catch (error) {
      return { error: String(error), resolved: {} };
    } finally {
      if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey: childSessionKey, deleteTranscript: true }); } catch { /* best effort */ } }
    }
  };
  api.on("agent_turn_prepare", async (event, ctx) => {
    const observedAt = Date.now();
    const memoryWorkspace = config.memory_workspace ?? config.statement_store_workspace;
    if (config.enabled === false || ctx.agentId === "nollm-dream-agent" || !ctx.sessionKey || !memoryWorkspace || !config.python_executable || !config.nollm_repo_root || !event.prompt.trim()) return;
    const model = configuredModel(ctx.modelProviderId && ctx.modelId ? `${ctx.modelProviderId}/${ctx.modelId}` : undefined);
    if (!usableModel(model)) return;
    const requestId = `recall-${createHash("sha256").update(`${ctx.sessionKey}\0${ctx.runId ?? event.prompt}`).digest("hex")}`;
    const operationStartedAt = Date.now();
    const timing: Record<string, number | string | boolean | null> = {
      surface_build_ms: 0, surface_order_count: 0, surface_projection_count: 0,
      surface_page_count: 0, physical_entry_resolution_ms: 0, recall_core_ms: 0,
      physical_entry_model_call_skipped: false, recall_agent_ms: 0,
      model_call_count: 0, invalid_decision_count: 0, correction_attempt_count: 0,
      correction_success: false, provider_timeout_stage: null,
      total_operation_ms: 0, timeout_stage: null,
    };
    let stageStartedAt = Date.now();
    let built = await bridge(config, { action: "build_recall_prompt", request_id: requestId, query: event.prompt, memory_workspace: memoryWorkspace, surface_budget: surfaceBudget(config, "recall") });
    timing.surface_build_ms = Date.now() - stageStartedAt;
    const firstSurface = built.surface as Record<string, unknown> | undefined;
    const statistics = firstSurface?.order_statistics as Record<string, unknown> | undefined;
    timing.surface_order_count = typeof firstSurface?.active_order === "number" ? firstSurface.active_order + 1 : 0;
    timing.surface_projection_count = typeof statistics?.occupied_cell_count === "number" ? statistics.occupied_cell_count : 0;
    timing.surface_page_count = typeof statistics?.estimated_pages === "number" ? statistics.estimated_pages : 0;
    const surfacePath: unknown[] = [];
    let traversal = 0;
    while (built.ok === true && (built.status === "traverse" || built.status === "physical_entry") && typeof built.prompt === "string" && traversal < (config.recall_surface_max_calls ?? 24)) {
      surfacePath.push(built.surface ?? built.physical_entries);
      const current = built;
      stageStartedAt = Date.now();
      let step = await runHiddenAgent(current.prompt as string, model!, `${requestId}:surface:${traversal}`);
      timing.model_call_count = Number(timing.model_call_count) + 1;
      timing.recall_agent_ms = Number(timing.recall_agent_ms) + Date.now() - stageStartedAt;
      if (!step.raw) { timing.timeout_stage = "recall_surface_agent"; timing.provider_timeout_stage = "recall_surface_agent"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "recall_surface_agent", request_id: requestId, error: step.error, hook_observed_at: observedAt, operation_timing: timing }); return; }
      stageStartedAt = Date.now();
      let advanced = await bridge(config, { action: "advance_recall_traversal", query: event.prompt, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: memoryWorkspace });
      while (traversalRetryable(advanced)) {
        timing.invalid_decision_count = Number(timing.invalid_decision_count) + 1;
        if (Number(timing.correction_attempt_count) >= TRAVERSAL_CORRECTION_MAX_ATTEMPTS) break;
        timing.correction_attempt_count = Number(timing.correction_attempt_count) + 1;
        stageStartedAt = Date.now();
        step = await runHiddenAgent(traversalCorrectionPrompt(current.prompt as string, step.raw, advanced, Number(timing.correction_attempt_count)), model!, `${requestId}:surface:${traversal}:correction:${timing.correction_attempt_count}`);
        timing.model_call_count = Number(timing.model_call_count) + 1;
        timing.recall_agent_ms = Number(timing.recall_agent_ms) + Date.now() - stageStartedAt;
        if (!step.raw) { timing.timeout_stage = "recall_traversal_correction"; timing.provider_timeout_stage = "recall_traversal_correction"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "recall_traversal_correction", request_id: requestId, error: step.error, operation_timing: timing }); return; }
        advanced = await bridge(config, { action: "advance_recall_traversal", query: event.prompt, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: memoryWorkspace });
        if (advanced.ok === true) timing.correction_success = true;
      }
      built = advanced;
      const accessTiming = built.operation_timing && typeof built.operation_timing === "object" ? built.operation_timing as Record<string, unknown> : {};
      if (typeof accessTiming.physical_entry_resolution_ms === "number") timing.physical_entry_resolution_ms = accessTiming.physical_entry_resolution_ms;
      if (typeof accessTiming.recall_core_ms === "number") timing.recall_core_ms = accessTiming.recall_core_ms;
      if (typeof accessTiming.physical_entry_model_call_skipped === "boolean") timing.physical_entry_model_call_skipped = accessTiming.physical_entry_model_call_skipped;
      traversal += 1;
    }
    if (built.ok === true && built.status === "complete_none") {
      timing.total_operation_ms = Date.now() - operationStartedAt;
      await trace(config, { status: "completed_none", stage: "recall", request_id: requestId, entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing });
      return;
    }
    if (built.ok !== true || built.status !== "recall_decision" || typeof built.prompt !== "string") {
      timing.timeout_stage = "recall_surface_terminal"; timing.total_operation_ms = Date.now() - operationStartedAt;
      await trace(config, { status: "defer", stage: "recall_surface_terminal", request_id: requestId, bridge_status: built.status, bridge_error: built.error, bridge_code: built.code, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing });
      return;
    }
    stageStartedAt = Date.now();
    const selected = await runHiddenAgent(built.prompt, model!, `${requestId}:recall-selection`);
    timing.model_call_count = Number(timing.model_call_count) + 1;
    timing.recall_agent_ms = Number(timing.recall_agent_ms) + Date.now() - stageStartedAt;
    if (!selected.raw) { timing.timeout_stage = "recall_agent"; timing.provider_timeout_stage = "recall_agent"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "recall_agent", request_id: requestId, error: selected.error, hook_observed_at: observedAt, operation_timing: timing }); return; }
    const rendered = await bridge(config, { action: "render_recall_injection", raw_model_response: selected.raw, candidates: built.candidates });
    timing.total_operation_ms = Date.now() - operationStartedAt;
    if (rendered.ok === true && rendered.outcome === "none") {
      await trace(config, { status: "completed_none", stage: "recall", request_id: requestId, entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing, ...selected.resolved });
      return;
    }
    if (rendered.ok !== true || rendered.outcome !== "inject" || typeof rendered.injection !== "string") return;
    await trace(config, { status: "completed", stage: "recall", request_id: requestId, selected_statement_ids: rendered.statement_ids, selected_paths: selectedRecallPaths(built.candidates, rendered.statement_ids), entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing, ...selected.resolved });
    return { appendContext: rendered.injection };
  });
  api.on("before_agent_run", (event, ctx) => {
    const observedAt = Date.now();
    if (config.enabled === false || !ctx.sessionKey || ctx.agentId === "nollm-dream-agent") { recordHandler("before_agent_run", observedAt, {}); return; }
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    current.runId = ctx.runId ?? current.runId;
    if (ctx.modelProviderId && ctx.modelId) current.resolvedModel = `${ctx.modelProviderId}/${ctx.modelId}`;
    pending.set(ctx.sessionKey, current);
    recordHandler("before_agent_run", observedAt, { session_key: ctx.sessionKey, run_id: ctx.runId, model_provider_id: ctx.modelProviderId, model_id: ctx.modelId });
  });
  api.on("message_received", (event, ctx) => {
    const observedAt = Date.now();
    if (config.enabled === false || !ctx.sessionKey || typeof event.content !== "string" || !event.content.trim()) return;
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    const content = wellFormedText(event.content.trim());
    const identity = event.messageId || `${event.runId ?? ctx.runId ?? ""}:${createHash("sha256").update(content).digest("hex")}`;
    if (!current.users.some(turn => turn.identity === identity)) current.users = [...current.users, { role: "user", content_utf8: content, identity } as UserObservation].slice(-2);
    else duplicateHookObservationCount += 1;
    current.runId = event.runId ?? ctx.runId ?? current.runId;
    pending.set(ctx.sessionKey, current);
    recordHandler("message_received", observedAt, { session_key: ctx.sessionKey, run_id: current.runId, message_id: event.messageId });
  });
  api.on("llm_output", (event, ctx) => {
    if (!ctx.sessionKey) return;
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    current.resolvedModel = event.resolvedRef ?? `${event.provider}/${event.model}`;
    current.runId = event.runId ?? current.runId;
    pending.set(ctx.sessionKey, current);
  });
  const launch = async (candidate: Candidate) => {
    const { sessionKey, assistant, sourceHook, observedAt, phase } = candidate;
    if (config.enabled === false || !assistant.trim() || inFlight.has(sessionKey)) return;
    if (!config.python_executable || !config.nollm_repo_root) { await trace(config, { status: "defer", reason: "explicit_configuration_required", trigger_phase: phase }); return; }
    const fallbackUsers: UserObservation[] = (candidate.users ?? []).map((turn, index) => ({ role: turn.role, content_utf8: turn.content_utf8, identity: `${candidate.runId ?? "fallback"}:${index}:${createHash("sha256").update(turn.content_utf8).digest("hex")}` }));
    const current = pending.get(sessionKey) ?? { users: fallbackUsers, resolvedModel: candidate.resolvedModel, runId: candidate.runId };
    if (!current.users.length && fallbackUsers.length) current.users = fallbackUsers;
    if (!current.resolvedModel && candidate.resolvedModel) current.resolvedModel = candidate.resolvedModel;
    if (!current?.users.length) return;
    const model = configuredModel(current.resolvedModel);
    if (!usableModel(model)) {
      await trace(config, { status: "defer", reason: "model_not_allowed", model }); return;
    }
    const key = turnKey(sessionKey, candidate.runId ?? current.runId, undefined, assistant);
    const idempotencyKey = createHash("sha256").update(`${key}\0${config.prompt_version ?? "dream-json-p1"}\0nollm_access_dream_formation_v1`).digest("hex");
    if (scheduled.has(idempotencyKey)) { duplicateDreamSuppressedCount += 1; return; }
    scheduled.add(idempotencyKey);
    const requestId = `dream-request-${idempotencyKey}`;
    const request = {
      request_id: requestId,
      material: { material_id: `material-${idempotencyKey}`, turns: boundedTurns(current.users, assistant, config.max_material_chars ?? 12000) },
      max_statements: config.max_statements ?? 8, max_statement_chars: config.max_statement_chars ?? 4096,
      max_total_chars: config.max_total_chars ?? 8192, schema_version: "nollm_access_dream_formation_v1",
    };
    const built = await bridge(config, { action: "build_dream_prompt", request, prompt_version: config.prompt_version ?? "dream-json-p1" });
    if (built.ok !== true || typeof built.prompt !== "string") { await trace(config, { status: "error", stage: "build_prompt", ...built }); return; }
    inFlight.add(sessionKey);
    const dreamStartedAt = Date.now();
    try {
      const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
      const override = config.model_mode === "dedicated" ? modelOverride(model) : undefined;
      childParents.set(childSessionKey, { parentRunId: candidate.runId ?? current.runId, requestedModel: model });
      const spawned = await api.runtime.subagent.run({
        sessionKey: childSessionKey, message: built.prompt,
        ...(override ?? {}),
        lightContext: true, deliver: false, idempotencyKey,
      });
      await trace(config, { status: "started", request_id: requestId, turn_key_sha256: createHash("sha256").update(key).digest("hex"), session_key: sessionKey, parent_run_id: candidate.runId ?? current.runId, child_session_key: childSessionKey, run_id: spawned.runId, requested_model: model, model_mode: config.model_mode ?? "inherit", prompt_version: built.prompt_version, prompt_sha256: built.prompt_sha256, schema_sha256: built.schema_sha256, source_hook: sourceHook, trigger_phase: phase, hook_observed_at: observedAt, background_scheduled_at: dreamStartedAt, prompt_build_started_at: dreamStartedAt, subagent_started_at: Date.now(), deliver: false, material: request.material, duplicate_hook_observation_count: duplicateHookObservationCount, duplicate_dream_suppressed_count: duplicateDreamSuppressedCount });
      void completeDream(api, config, sessionKey, childSessionKey, spawned.runId, request, built, inFlight, dreamStartedAt, idempotencyKey, model);
    } catch (error) {
      inFlight.delete(sessionKey);
      await trace(config, { status: "error", stage: "spawn", request_id: requestId, error: String(error), trigger_phase: phase });
    }
  };
  api.on("message_sent", (event, ctx) => {
    const observedAt = Date.now();
    const sessionKey = ctx.sessionKey ?? event.sessionKey;
    if (!event.success || !sessionKey || !event.content.trim()) { recordHandler("message_sent", observedAt, { success: event.success }); return; }
    const current = pending.get(sessionKey); const runId = event.runId ?? ctx.runId ?? current?.runId;
    queue(() => { void launch({ sessionKey, runId, assistant: wellFormedText(event.content), phase: "AFTER_DELIVERY", sourceHook: "message_sent", observedAt }); });
    recordHandler("message_sent", observedAt, { session_key: sessionKey, run_id: runId, trigger_phase: "AFTER_DELIVERY", success: true });
  });
  api.on("agent_end", (event, ctx) => {
    const observedAt = Date.now();
    if (!event.success || !ctx.sessionKey || ctx.agentId === "nollm-dream-agent") return;
    const assistant = extractAssistantText(event.messages);
    if (!assistant) return;
    const model = ctx.modelProviderId && ctx.modelId ? `${ctx.modelProviderId}/${ctx.modelId}` : undefined;
    const content = wellFormedText(assistant);
    const runId = event.runId ?? ctx.runId;
    queue(() => { void launch({ sessionKey: ctx.sessionKey!, runId, assistant: content, phase: "AFTER_TURN", sourceHook: "agent_end", observedAt, users: extractUserTurns(event.messages), resolvedModel: model }); });
    recordHandler("agent_end", observedAt, { session_key: ctx.sessionKey, run_id: runId, trigger_phase: "AFTER_TURN", success: true });
  });
  api.on("subagent_spawned", (event) => {
    const parent = childParents.get(event.childSessionKey);
    if (!parent) return;
    queue(() => { void trace(config, { status: "subagent_spawned", parent_run_id: parent.parentRunId, child_run_id: event.runId, child_session_key: event.childSessionKey, requested_model: parent.requestedModel, resolved_provider: event.resolvedProvider, resolved_model: event.resolvedModel, observed_at: Date.now() }); });
  });
  api.on("subagent_ended", (event, ctx) => {
    if (!ctx.childSessionKey || !childParents.has(ctx.childSessionKey)) return;
    queue(() => { void trace(config, { status: "subagent_ended", child_run_id: event.runId ?? ctx.runId, child_session_key: ctx.childSessionKey, outcome: event.outcome, ended_at: event.endedAt, reason: event.reason }); });
  });
}

async function completeDream(api: OpenClawPluginApi, config: DreamConfig, parentSession: string, childSession: string, runId: string, request: object, built: Record<string, unknown>, inFlight: Set<string>, startedAt: number, stableId: string, model?: string): Promise<void> {
  try {
    const waited = await api.runtime.subagent.waitForRun({ runId, timeoutMs: config.timeout_ms ?? 120000 });
    if (waited.status !== "ok") { const completedAt = Date.now(); await trace(config, { status: waited.status, stage: "subagent", run_id: runId, error: waited.error, dream_completed_at: completedAt, dream_latency_ms: completedAt - startedAt, visible_message_count: 0 }); return; }
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSession, limit: 20 });
    const raw = extractAssistantText(session.messages);
    const resolved = extractResolvedModel(session.messages);
    if (!raw) { await trace(config, { status: "error", stage: "empty_output", run_id: runId, dream_completed_at: Date.now(), ...resolved, visible_message_count: 0 }); return; }
    let parsed = await parseDreamAttempt(config, request, raw, `dream-result-${stableId}`, "initial", runId, parentSession, startedAt, resolved, built.prompt_version);
    if (formationRetryable(parsed)) {
      const repaired = await runFormatRepair(api, config, raw, String(parsed.error ?? "invalid_json"), model, stableId);
      if (repaired) parsed = await parseDreamAttempt(config, request, repaired.raw, `dream-result-${stableId}`, "format_repair", repaired.runId, parentSession, startedAt, repaired.resolved, "dream-format-repair-v1");
    }
    for (const version of ["dream-json-p1", "dream-json-p2"]) {
      if (!formationRetryable(parsed)) break;
      const retry = await runFullDreamRetry(api, config, request, version, model, stableId);
      if (retry) parsed = await parseDreamAttempt(config, request, retry.raw, `dream-result-${stableId}`, version, retry.runId, parentSession, startedAt, retry.resolved, version);
    }
    if (shouldApplyPlacement(config, parsed, model)) {
      for (const statement of parsed.statements as unknown[]) await completePlacement(api, config, parentSession, statement, model!, stableId, Date.now() - startedAt);
    }
  } catch (error) {
    await trace(config, { status: "error", stage: "completion", run_id: runId, dream_completed_at: Date.now(), error: String(error), visible_message_count: 0 });
  } finally {
    inFlight.delete(parentSession);
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey: childSession, deleteTranscript: true }); } catch { /* diagnostic cleanup is best effort */ } }
  }
}

type DreamAttempt = { raw: string; runId: string; resolved: Record<string, string> };

function outputEvidence(raw: string): Record<string, unknown> {
  const limit = 24000;
  return {
    raw_visible_output: raw.slice(0, limit), raw_visible_output_truncated: raw.length > limit,
    raw_visible_output_chars: raw.length, raw_visible_output_sha256: createHash("sha256").update(raw).digest("hex"),
  };
}

export function formationRetryable(parsed: Record<string, unknown>): boolean {
  return parsed.ok !== true && ["invalid_json", "invalid_schema", "invalid_dream_result"].includes(String(parsed.error ?? ""));
}

export function placementRetryable(parsed: Record<string, unknown>): boolean {
  return parsed.ok !== true && ["invalid_json", "invalid_schema"].includes(String(parsed.error ?? ""));
}

export function traversalRetryable(parsed: Record<string, unknown>): boolean {
  return parsed.ok !== true && ["invalid_json", "invalid_surface_traversal"].includes(String(parsed.error ?? ""));
}

export function traversalCorrectionPrompt(originalPrompt: string, raw: string, parsed: Record<string, unknown>, attempt: number): string {
  const rejected = JSON.stringify(raw).slice(0, 4096);
  return `${originalPrompt}\n\nCorrection attempt ${attempt} of ${TRAVERSAL_CORRECTION_MAX_ATTEMPTS}. The previous response was rejected without changing traversal or memory state. Error: ${String(parsed.message ?? parsed.error ?? "invalid traversal decision")}. Rejected response: ${rejected}. Return exactly one action from the legal action list above, using a currently visible candidate_id when required.`;
}

export function shouldApplyPlacement(config: DreamConfig, parsed: Record<string, unknown>, model?: string): boolean {
  return parsed.ok === true && config.write_mode === "statement-store" && Boolean(config.statement_store_workspace) && Boolean(model) && Array.isArray(parsed.statements);
}

async function parseDreamAttempt(config: DreamConfig, request: object, raw: string, resultId: string, attempt: string, runId: string, parentSession: string, startedAt: number, resolved: Record<string, string>, promptVersion: unknown): Promise<Record<string, unknown>> {
  // Placement owns the first persistent write so a rejected placement cannot leave an orphan Statement.
  const parsed = await bridge(config, { action: "parse_dream_result", request, raw_model_response: raw, result_id: resultId, statement_store_workspace: null });
  const completedAt = Date.now();
  await trace(config, { status: parsed.ok === true ? "completed" : "error", stage: "parse_store", formation_attempt: attempt, run_id: runId, parent_session_key: parentSession, dream_completed_at: completedAt, dream_latency_ms: completedAt - startedAt, ...resolved, write_mode: config.write_mode ?? "shadow", visible_message_count: 0, python_semantic_fallback: false, prompt_version: promptVersion, ...outputEvidence(raw), ...parsed });
  return parsed;
}

async function runFormatRepair(api: OpenClawPluginApi, config: DreamConfig, raw: string, failure: string, model: string | undefined, stableId: string): Promise<DreamAttempt | undefined> {
  const built = await bridge(config, { action: "build_dream_format_repair_prompt", raw_model_response: raw, failure });
  if (built.ok !== true || typeof built.prompt !== "string") return undefined;
  return runDreamSubagent(api, config, built.prompt, model, `${stableId}:format-repair`);
}

async function runFullDreamRetry(api: OpenClawPluginApi, config: DreamConfig, request: object, version: string, model: string | undefined, stableId: string): Promise<DreamAttempt | undefined> {
  const built = await bridge(config, { action: "build_dream_prompt", request, prompt_version: version });
  if (built.ok !== true || typeof built.prompt !== "string") return undefined;
  return runDreamSubagent(api, config, built.prompt, model, `${stableId}:${version}`);
}

async function runDreamSubagent(api: OpenClawPluginApi, config: DreamConfig, prompt: string, model: string | undefined, idempotencyKey: string): Promise<DreamAttempt | undefined> {
  const sessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
  const override = config.model_mode === "dedicated" && model ? modelOverride(model) : undefined;
  try {
    const spawned = await api.runtime.subagent.run({ sessionKey, message: prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey });
    const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
    if (waited.status !== "ok") return undefined;
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey, limit: 20 });
    const raw = extractAssistantText(session.messages);
    return raw ? { raw, runId: spawned.runId, resolved: extractResolvedModel(session.messages) } : undefined;
  } finally {
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey, deleteTranscript: true }); } catch { /* diagnostic cleanup is best effort */ } }
  }
}

async function completePlacement(api: OpenClawPluginApi, config: DreamConfig, sessionKey: string, statement: unknown, model: string, stableId: string, formationMs: number): Promise<void> {
  const operationStartedAt = Date.now();
  const timing: Record<string, number | string | boolean | null> = {
    formation_ms: formationMs, statement_persist_ms: 0, surface_build_ms: 0,
    surface_order_count: 0, surface_projection_count: 0, surface_page_count: 0,
    placement_prompt_build_ms: 0, placement_subagent_ms: 0, placement_json_repair_ms: 0,
    physical_entry_resolution_ms: 0, physical_entry_model_call_skipped: false,
    decision_validation_ms: 0, placement_apply_ms: 0, handle_bind_ms: 0,
    model_call_count: 0, invalid_decision_count: 0, correction_attempt_count: 0,
    correction_success: false, provider_timeout_stage: null,
    total_operation_ms: 0, timeout_stage: null,
  };
  const statementId = statement && typeof statement === "object" && typeof (statement as Record<string, unknown>).statement_id === "string" ? (statement as Record<string, unknown>).statement_id : "unknown";
  const requestId = `placement-${createHash("sha256").update(`${stableId}\0${statementId}`).digest("hex")}`;
  let stageStartedAt = Date.now();
  let built = await bridge(config, { action: "build_placement_prompt", request_id: requestId, statement, memory_workspace: config.memory_workspace ?? config.statement_store_workspace, surface_budget: surfaceBudget(config, "placement") });
  timing.surface_build_ms = Date.now() - stageStartedAt;
  const firstSurface = built.surface as Record<string, unknown> | undefined;
  const statistics = firstSurface?.order_statistics as Record<string, unknown> | undefined;
  timing.surface_order_count = typeof firstSurface?.active_order === "number" ? firstSurface.active_order + 1 : 0;
  timing.surface_projection_count = typeof statistics?.occupied_cell_count === "number" ? statistics.occupied_cell_count : 0;
  timing.surface_page_count = typeof statistics?.estimated_pages === "number" ? statistics.estimated_pages : 0;
  const surfacePath: unknown[] = [];
  let traversal = 0;
  while (built.ok === true && (built.status === "traverse" || built.status === "physical_entry") && typeof built.prompt === "string" && traversal < (config.placement_surface_max_calls ?? 32)) {
    surfacePath.push(built.surface ?? built.physical_entries);
    const current = built;
    stageStartedAt = Date.now();
    let step = await runDreamSubagent(api, config, current.prompt as string, model, `${requestId}:surface:${traversal}`);
    timing.model_call_count = Number(timing.model_call_count) + 1;
    timing.placement_subagent_ms = Number(timing.placement_subagent_ms) + Date.now() - stageStartedAt;
    if (!step?.raw) { timing.timeout_stage = "placement_surface_agent"; timing.provider_timeout_stage = "placement_surface_agent"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "placement_surface_agent", request_id: requestId, operation_timing: timing }); return; }
    stageStartedAt = Date.now();
    let advanced = await bridge(config, { action: "advance_placement_traversal", statement, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: config.memory_workspace ?? config.statement_store_workspace });
    while (traversalRetryable(advanced)) {
      timing.invalid_decision_count = Number(timing.invalid_decision_count) + 1;
      if (Number(timing.correction_attempt_count) >= TRAVERSAL_CORRECTION_MAX_ATTEMPTS) break;
      timing.correction_attempt_count = Number(timing.correction_attempt_count) + 1;
      stageStartedAt = Date.now();
      step = await runDreamSubagent(api, config, traversalCorrectionPrompt(current.prompt as string, step.raw, advanced, Number(timing.correction_attempt_count)), model, `${requestId}:surface:${traversal}:correction:${timing.correction_attempt_count}`);
      timing.model_call_count = Number(timing.model_call_count) + 1;
      timing.placement_subagent_ms = Number(timing.placement_subagent_ms) + Date.now() - stageStartedAt;
      if (!step?.raw) { timing.timeout_stage = "placement_traversal_correction"; timing.provider_timeout_stage = "placement_traversal_correction"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "placement_traversal_correction", request_id: requestId, operation_timing: timing }); return; }
      advanced = await bridge(config, { action: "advance_placement_traversal", statement, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: config.memory_workspace ?? config.statement_store_workspace });
      if (advanced.ok === true) timing.correction_success = true;
    }
    built = advanced;
    const bridgeMs = Date.now() - stageStartedAt;
    timing.placement_prompt_build_ms = Number(timing.placement_prompt_build_ms) + bridgeMs;
    const accessTiming = built.operation_timing && typeof built.operation_timing === "object" ? built.operation_timing as Record<string, unknown> : {};
    if (typeof accessTiming.physical_entry_resolution_ms === "number") timing.physical_entry_resolution_ms = accessTiming.physical_entry_resolution_ms;
    if (typeof accessTiming.physical_entry_model_call_skipped === "boolean") timing.physical_entry_model_call_skipped = accessTiming.physical_entry_model_call_skipped;
    traversal += 1;
  }
  if (built.ok !== true || built.status !== "placement_decision" || typeof built.prompt !== "string") { timing.timeout_stage = "placement_prompt"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "placement_prompt", request_id: requestId, surface_path: surfacePath, operation_timing: timing, ...built }); return; }
  const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
  const override = config.model_mode === "dedicated" ? modelOverride(model) : undefined;
  try {
    stageStartedAt = Date.now();
    const spawned = await api.runtime.subagent.run({ sessionKey: childSessionKey, message: built.prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey: `${requestId}:agent` });
    const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
    timing.placement_subagent_ms = Number(timing.placement_subagent_ms) + Date.now() - stageStartedAt;
    timing.model_call_count = Number(timing.model_call_count) + 1;
    if (waited.status !== "ok") { timing.timeout_stage = "placement_agent"; timing.provider_timeout_stage = "placement_agent"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "placement_agent", request_id: requestId, error: waited.error ?? waited.status, operation_timing: timing }); return; }
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSessionKey, limit: 20 });
    const raw = extractAssistantText(session.messages);
    if (!raw) { timing.timeout_stage = "placement_agent"; timing.provider_timeout_stage = "placement_agent"; timing.total_operation_ms = Date.now() - operationStartedAt; await trace(config, { status: "defer", stage: "placement_agent", request_id: requestId, error: "empty_output", operation_timing: timing }); return; }
    stageStartedAt = Date.now();
    let applied = await applyPlacementAttempt(config, requestId, raw, statement, built.selected_entry);
    timing.placement_apply_ms = Date.now() - stageStartedAt;
    let attemptKind = "initial";
    if (placementRetryable(applied)) {
      stageStartedAt = Date.now();
      const repaired = await runFormatRepair(api, config, raw, String(applied.error ?? "invalid_json"), model, `${requestId}:format-repair`);
      if (repaired) timing.model_call_count = Number(timing.model_call_count) + 1;
      timing.placement_json_repair_ms = Date.now() - stageStartedAt;
      if (repaired) {
        applied = await applyPlacementAttempt(config, requestId, repaired.raw, statement, built.selected_entry);
        attemptKind = "format_repair";
      }
    }
    for (let index = 1; index <= 2 && placementRetryable(applied); index += 1) {
      const retry = await runDreamSubagent(api, config, String(built.prompt), model, `${requestId}:retry:${index}`);
      timing.model_call_count = Number(timing.model_call_count) + 1;
      if (!retry) break;
      applied = await applyPlacementAttempt(config, requestId, retry.raw, statement, built.selected_entry);
      attemptKind = `full_retry_${index}`;
    }
    const accessTiming = applied.operation_timing && typeof applied.operation_timing === "object" ? applied.operation_timing as Record<string, number> : {};
    for (const key of ["statement_persist_ms", "decision_validation_ms", "placement_apply_ms", "handle_bind_ms"]) if (typeof accessTiming[key] === "number") timing[key] = accessTiming[key];
    timing.total_operation_ms = Date.now() - operationStartedAt;
    if (applied.ok !== true) timing.timeout_stage = "placement_apply";
    await trace(config, { status: applied.ok === true ? "completed" : "error", stage: "placement_apply", placement_attempt: attemptKind, request_id: requestId, surface_path: surfacePath, visible_message_count: 0, ...applied, operation_timing: timing, ...extractResolvedModel(session.messages) });
  } catch (error) {
    timing.timeout_stage = "placement"; timing.total_operation_ms = Date.now() - operationStartedAt;
    await trace(config, { status: "error", stage: "placement", request_id: requestId, error: String(error), operation_timing: timing });
  } finally {
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey: childSessionKey, deleteTranscript: true }); } catch { /* best effort */ } }
  }
}

async function applyPlacementAttempt(config: DreamConfig, requestId: string, raw: string, statement: unknown, selectedEntry: unknown): Promise<Record<string, unknown>> {
  return bridge(config, {
    action: "apply_placement", request_id: requestId, raw_model_response: raw, statement,
    selected_entry: selectedEntry, memory_workspace: config.memory_workspace ?? config.statement_store_workspace,
  });
}

export function extractResolvedModel(messages: unknown[]): Record<string, string> {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (!message || typeof message !== "object") continue;
    const value = message as Record<string, unknown>;
    if (value.role !== "assistant") continue;
    const provider = typeof value.provider === "string" ? value.provider : undefined;
    const model = typeof value.model === "string" ? value.model : undefined;
    if (provider && model) return { resolved_provider: provider, resolved_model: model, resolved_model_ref: `${provider}/${model}` };
  }
  return {};
}

const plugin = definePluginEntry({
  id: "nollm-formation", name: "Nollm Invisible Dream Agent",
  description: "Post-delivery background MemoryStatement formation through an OpenClaw-owned subagent.",
  configSchema: buildJsonPluginConfigSchema(JSON_SCHEMA),
  register: registerDreamAgent,
});

export default plugin;
