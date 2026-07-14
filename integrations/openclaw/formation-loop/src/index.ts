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
  geometry_profile?: "default_dream_v1"; geometry_contract_version?: "nollm_translation_covariant_physical_coverage_v1";
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
    geometry_profile: { type: "string", const: "default_dream_v1", default: "default_dream_v1" }, geometry_contract_version: { type: "string", const: "nollm_translation_covariant_physical_coverage_v1", default: "nollm_translation_covariant_physical_coverage_v1" },
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
    let built = await bridge(config, { action: "build_recall_prompt", request_id: requestId, query: event.prompt, memory_workspace: memoryWorkspace, surface_budget: surfaceBudget(config, "recall") });
    const surfacePath: unknown[] = [];
    let traversal = 0;
    while (built.ok === true && built.status === "traverse" && typeof built.prompt === "string" && traversal < (config.recall_surface_max_calls ?? 24)) {
      surfacePath.push(built.surface);
      const step = await runHiddenAgent(built.prompt, model!, `${requestId}:surface:${traversal}`);
      if (!step.raw) { await trace(config, { status: "defer", stage: "recall_surface_agent", request_id: requestId, error: step.error, hook_observed_at: observedAt }); return; }
      built = await bridge(config, { action: "advance_recall_traversal", query: event.prompt, traversal_state: built.traversal_state, raw_model_response: step.raw, memory_workspace: memoryWorkspace });
      traversal += 1;
    }
    if (built.ok === true && built.status === "complete_none") {
      await trace(config, { status: "completed_none", stage: "recall", request_id: requestId, entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0 });
      return;
    }
    if (built.ok !== true || built.status !== "recall_decision" || typeof built.prompt !== "string") {
      await trace(config, { status: "defer", stage: "recall_surface_terminal", request_id: requestId, bridge_status: built.status, bridge_error: built.error, bridge_code: built.code, surface_path: surfacePath, visible_message_count: 0 });
      return;
    }
    const selected = await runHiddenAgent(built.prompt, model!, `${requestId}:recall-selection`);
    if (!selected.raw) { await trace(config, { status: "defer", stage: "recall_agent", request_id: requestId, error: selected.error, hook_observed_at: observedAt }); return; }
    const rendered = await bridge(config, { action: "render_recall_injection", raw_model_response: selected.raw, candidates: built.candidates });
    if (rendered.ok === true && rendered.outcome === "none") {
      await trace(config, { status: "completed_none", stage: "recall", request_id: requestId, entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, ...selected.resolved });
      return;
    }
    if (rendered.ok !== true || rendered.outcome !== "inject" || typeof rendered.injection !== "string") return;
    await trace(config, { status: "completed", stage: "recall", request_id: requestId, selected_statement_ids: rendered.statement_ids, selected_paths: selectedRecallPaths(built.candidates, rendered.statement_ids), entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, ...selected.resolved });
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
      for (const statement of parsed.statements as unknown[]) await completePlacement(api, config, parentSession, statement, model!, stableId);
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

async function completePlacement(api: OpenClawPluginApi, config: DreamConfig, sessionKey: string, statement: unknown, model: string, stableId: string): Promise<void> {
  const statementId = statement && typeof statement === "object" && typeof (statement as Record<string, unknown>).statement_id === "string" ? (statement as Record<string, unknown>).statement_id : "unknown";
  const requestId = `placement-${createHash("sha256").update(`${stableId}\0${statementId}`).digest("hex")}`;
  let built = await bridge(config, { action: "build_placement_prompt", request_id: requestId, statement, memory_workspace: config.memory_workspace ?? config.statement_store_workspace, surface_budget: surfaceBudget(config, "placement") });
  const surfacePath: unknown[] = [];
  let traversal = 0;
  while (built.ok === true && built.status === "traverse" && typeof built.prompt === "string" && traversal < (config.placement_surface_max_calls ?? 32)) {
    surfacePath.push(built.surface);
    const step = await runDreamSubagent(api, config, built.prompt, model, `${requestId}:surface:${traversal}`);
    if (!step?.raw) { await trace(config, { status: "defer", stage: "placement_surface_agent", request_id: requestId }); return; }
    built = await bridge(config, { action: "advance_placement_traversal", statement, traversal_state: built.traversal_state, raw_model_response: step.raw, memory_workspace: config.memory_workspace ?? config.statement_store_workspace });
    traversal += 1;
  }
  if (built.ok !== true || built.status !== "placement_decision" || typeof built.prompt !== "string") { await trace(config, { status: "defer", stage: "placement_prompt", request_id: requestId, surface_path: surfacePath, ...built }); return; }
  const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
  const override = config.model_mode === "dedicated" ? modelOverride(model) : undefined;
  try {
    const spawned = await api.runtime.subagent.run({ sessionKey: childSessionKey, message: built.prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey: `${requestId}:agent` });
    const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
    if (waited.status !== "ok") { await trace(config, { status: "defer", stage: "placement_agent", request_id: requestId, error: waited.error ?? waited.status }); return; }
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSessionKey, limit: 20 });
    const raw = extractAssistantText(session.messages);
    if (!raw) { await trace(config, { status: "defer", stage: "placement_agent", request_id: requestId, error: "empty_output" }); return; }
    let applied = await applyPlacementAttempt(config, requestId, raw, statement, built.selected_entry);
    let attemptKind = "initial";
    if (placementRetryable(applied)) {
      const repaired = await runFormatRepair(api, config, raw, String(applied.error ?? "invalid_json"), model, `${requestId}:format-repair`);
      if (repaired) {
        applied = await applyPlacementAttempt(config, requestId, repaired.raw, statement, built.selected_entry);
        attemptKind = "format_repair";
      }
    }
    for (let index = 1; index <= 2 && placementRetryable(applied); index += 1) {
      const retry = await runDreamSubagent(api, config, String(built.prompt), model, `${requestId}:retry:${index}`);
      if (!retry) break;
      applied = await applyPlacementAttempt(config, requestId, retry.raw, statement, built.selected_entry);
      attemptKind = `full_retry_${index}`;
    }
    await trace(config, { status: applied.ok === true ? "completed" : "error", stage: "placement_apply", placement_attempt: attemptKind, request_id: requestId, surface_path: surfacePath, visible_message_count: 0, ...applied, ...extractResolvedModel(session.messages) });
  } catch (error) {
    await trace(config, { status: "error", stage: "placement", request_id: requestId, error: String(error) });
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
