import { spawn } from "node:child_process";
import { appendFile, mkdir } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { AsyncResource } from "node:async_hooks";
import { dirname, join } from "node:path";
import { Type } from "typebox";
import { buildJsonPluginConfigSchema, definePluginEntry, type OpenClawPluginApi } from "openclaw/plugin-sdk/core";
import { appendLatencyEvent, COMMIT_LATENCY_SCHEMA, durationMs, durationUs, RECALL_LATENCY_SCHEMA, sha256Text, systemLatencyClock, turnCorrelationId } from "./latency.js";
import { AbsorptionWorker, buildCaptureSourceWindowGroups, CAPTURE_PLUGIN_VERSION, CaptureStore, type AbsorptionResult, type CaptureContinuation, type CaptureEvaluationIdentity, type CaptureRecord, type CaptureStateEvent, type MemoryToolAction } from "./capture.js";

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
  revision_confirmation_schema_version?: "nollm_openclaw_revision_confirmation_v1";
  revision_confirmation_max_calls?: 1; revision_redecision_max_calls?: 1;
  revision_confirmation_model_mode?: "inherit";
  model_mode?: "inherit" | "dedicated"; model?: string; allowed_models?: string[];
  prompt_version?: string; timeout_ms?: number; max_material_chars?: number;
  max_statements?: number; max_statement_chars?: number; max_total_chars?: number;
  persist_subagent_transcripts?: boolean; debug_trace?: boolean; evidence_path?: string; evidence_run_id?: string;
  latency_validation_enabled?: boolean; latency_evidence_path?: string; latency_scenario_id?: string; latency_validation_run_id?: string;
  capture_enabled?: boolean; capture_workspace?: string; capture_scope_id?: string;
  capture_single_user_mode?: true;
  memory_scope_mode?: "single-configured-scope";
  absorption_enabled?: boolean; absorption_batch_max_captures?: number; absorption_batch_max_chars?: number; absorption_max_wait_ms?: number; absorption_stale_claim_ms?: number; absorption_retry_backoff_ms?: number; absorption_directive_finalization_ms?: number;
  writer_context_max_captures?: number; writer_context_max_chars?: number;
  writer_source_window_bytes?: number; writer_source_group_bytes?: number; writer_source_overlap_codepoints?: number; writer_max_continuation_passes?: number;
  proposition_writer_schema_version?: "nollm_openclaw_content_neutral_proposition_writer_v4";
  field_cartographer_schema_version?: "nollm_openclaw_field_cartographer_v2";
  cartographer_max_regions?: 32; cartographer_max_prompt_bytes?: 65536; cartographer_max_turns?: 4;
  pending_fallback_enabled?: boolean; pending_fallback_max_captures?: number; pending_fallback_max_chars?: number; pending_fallback_max_age_ms?: number;
  recall_hidden_call_budget?: 0;
  main_agent_recall_enabled?: boolean;
  main_agent_operation_ttl_ms?: number;
  surface_page_size?: number; surface_max_order?: number; surface_page_overhead_units?: number; surface_cell_preview_units?: number;
  recall_atlas_max_regions?: number;
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
    revision_confirmation_schema_version: { type: "string", const: "nollm_openclaw_revision_confirmation_v1", default: "nollm_openclaw_revision_confirmation_v1" },
    revision_confirmation_max_calls: { type: "integer", const: 1, default: 1 },
    revision_redecision_max_calls: { type: "integer", const: 1, default: 1 },
    revision_confirmation_model_mode: { type: "string", const: "inherit", default: "inherit" },
    model_mode: { type: "string", enum: ["inherit", "dedicated"], default: "inherit" }, model: { type: "string" },
    allowed_models: { type: "array", items: { type: "string" }, default: [] }, prompt_version: { type: "string", default: "dream-json-p1" },
    timeout_ms: { type: "integer", minimum: 1000, default: 120000 }, max_material_chars: { type: "integer", minimum: 1, default: 12000 },
    max_statements: { type: "integer", minimum: 1, default: 8 }, max_statement_chars: { type: "integer", minimum: 1, default: 4096 },
    max_total_chars: { type: "integer", minimum: 1, default: 8192 }, persist_subagent_transcripts: { type: "boolean", const: false, default: false },
    debug_trace: { type: "boolean", default: false }, evidence_path: { type: "string" }, evidence_run_id: { type: "string" },
    latency_validation_enabled: { type: "boolean", default: false }, latency_evidence_path: { type: "string" },
    latency_scenario_id: { type: "string" }, latency_validation_run_id: { type: "string" },
    capture_enabled: { type: "boolean", default: true }, capture_workspace: { type: "string" }, capture_scope_id: { type: "string", default: "local-default-user" },
    capture_single_user_mode: { type: "boolean", const: true, default: true },
    memory_scope_mode: { type: "string", const: "single-configured-scope", default: "single-configured-scope" },
    absorption_enabled: { type: "boolean", default: true }, absorption_batch_max_captures: { type: "integer", minimum: 1, maximum: 16, default: 4 },
    absorption_batch_max_chars: { type: "integer", minimum: 1, default: 24000 }, absorption_max_wait_ms: { type: "integer", minimum: 0, default: 250 },
    absorption_stale_claim_ms: { type: "integer", minimum: 1000, default: 300000 },
    absorption_retry_backoff_ms: { type: "integer", minimum: 100, default: 1000 },
    absorption_directive_finalization_ms: { type: "integer", minimum: 1000, default: 30000 },
    writer_context_max_captures: { type: "integer", minimum: 0, maximum: 4, default: 4 },
    writer_context_max_chars: { type: "integer", minimum: 0, maximum: 6000, default: 6000 },
    writer_source_window_bytes: { type: "integer", minimum: 1024, maximum: 24000, default: 12000 },
    writer_source_group_bytes: { type: "integer", minimum: 12000, maximum: 40000, default: 32000 },
    writer_source_overlap_codepoints: { type: "integer", minimum: 0, maximum: 1024, default: 128 },
    writer_max_continuation_passes: { type: "integer", minimum: 1, maximum: 32, default: 16 },
    locality_atlas_candidate_limit: { type: "integer", minimum: 1, maximum: 512, default: 512 },
    proposition_writer_schema_version: { type: "string", const: "nollm_openclaw_content_neutral_proposition_writer_v4", default: "nollm_openclaw_content_neutral_proposition_writer_v4" },
    field_cartographer_schema_version: { type: "string", const: "nollm_openclaw_field_cartographer_v2", default: "nollm_openclaw_field_cartographer_v2" },
    cartographer_max_regions: { type: "integer", const: 32, default: 32 },
    cartographer_max_prompt_bytes: { type: "integer", const: 65536, default: 65536 },
    cartographer_max_turns: { type: "integer", const: 4, default: 4 },
    pending_fallback_enabled: { type: "boolean", default: true }, pending_fallback_max_captures: { type: "integer", minimum: 1, maximum: 16, default: 4 },
    pending_fallback_max_chars: { type: "integer", minimum: 1, default: 6000 }, pending_fallback_max_age_ms: { type: "integer", minimum: 1000, default: 604800000 },
    recall_hidden_call_budget: { type: "integer", const: 0, default: 0 },
    main_agent_recall_enabled: { type: "boolean", default: true },
    main_agent_operation_ttl_ms: { type: "integer", minimum: 1000, maximum: 3600000, default: 300000 },
    surface_page_size: { type: "integer", minimum: 1, maximum: 8, default: 8 }, surface_max_order: { type: "integer", minimum: 0, maximum: 8, default: 8 },
    surface_page_overhead_units: { type: "integer", minimum: 1, default: 8 }, surface_cell_preview_units: { type: "integer", minimum: 1, default: 4 },
    recall_surface_max_pages: { type: "integer", minimum: 1, default: 4 }, recall_surface_max_cells: { type: "integer", minimum: 1, default: 32 }, recall_surface_max_projection_units: { type: "integer", minimum: 1, default: 160 }, recall_surface_max_calls: { type: "integer", minimum: 1, default: 24 },
    recall_atlas_max_regions: { type: "integer", minimum: 1, maximum: 32, default: 32 },
    placement_surface_max_pages: { type: "integer", minimum: 1, default: 6 }, placement_surface_max_cells: { type: "integer", minimum: 1, default: 48 }, placement_surface_max_projection_units: { type: "integer", minimum: 1, default: 240 }, placement_surface_max_calls: { type: "integer", minimum: 1, default: 32 },
  },
} as const;

export const TRAVERSAL_CORRECTION_MAX_ATTEMPTS = 2;
export const REVISION_CONFIRMATION_MAX_CALLS = 1;
export const REVISION_REDECISION_MAX_CALLS = 1;

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
type Candidate = { sessionKey: string; runId?: string; assistant: string; phase: TriggerPhase; sourceHook: "message_sent" | "agent_end"; observedAt: number; observedMonoNs: bigint; users?: Turn[]; resolvedModel?: string };
type PendingRecallLatency = { requestId: string; mainRunId?: string; queryPrepareEpochMs: number; injectionReadyEpochMs: number; outcome: "inject" | "none"; injectionHash?: string };
type MainAgentRunScope = { sessionKey: string; runId: string; scopeId: string; workspaceId: string };
type HostToolBinding = MainAgentRunScope & { toolName: string; input: unknown; observedEpochMs: number };
type MainAgentRecallOperation = {
  scope: MainAgentRunScope;
  createdAt: number;
  lastUsedAt: number;
  expiresAt: number;
  coreStateSha256: string;
  atlasFingerprint: string;
  pageFingerprint: string;
  policy: Record<string, number>;
  page: Record<string, unknown>;
  entries: Map<string, Record<string, unknown>>;
  regions: Map<string, string>;
  selectedEntryId?: string;
  selectedRegionId?: string;
  expanded: boolean;
};
type RunMemoryUseState = {
  scope: MainAgentRunScope;
  actions: Set<MemoryToolAction>;
  selectedEntryId?: string;
  recalledStatementIds: Set<string>;
  toolEvidenceIds: Set<string>;
  sequence: number;
  finalized: boolean;
};

// Gateway hook dispatch can cross plugin registration instances within one turn.
const pendingRecallLatencyByRun = new Map<string, PendingRecallLatency>();

export function mainAgentRunKey(scope: MainAgentRunScope): string {
  return `${scope.sessionKey}\0${scope.runId}\0${scope.scopeId}\0${scope.workspaceId}`;
}

export function reserveMainAgentOperationSlot<T extends { createdAt: number; expiresAt: number }>(
  operations: Map<string, T>, now: number, capacity = 64,
): string[] {
  const removed: string[] = [];
  for (const [operationId, operation] of operations) {
    if (operation.expiresAt <= now) {
      operations.delete(operationId);
      removed.push(operationId);
    }
  }
  while (operations.size >= capacity) {
    const oldest = [...operations.entries()].sort((left, right) => left[1].createdAt - right[1].createdAt)[0]?.[0];
    if (!oldest) break;
    operations.delete(oldest);
    removed.push(oldest);
  }
  return removed;
}

function sameMainAgentRun(left: MainAgentRunScope, right: MainAgentRunScope): boolean {
  return mainAgentRunKey(left) === mainAgentRunKey(right);
}

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

export function extractAssistantTextExact(messages: unknown[]): string | undefined {
  for (const item of [...messages].reverse()) {
    if (!item || typeof item !== "object") continue;
    const value = item as Record<string, unknown>;
    if (value.role !== "assistant") continue;
    if (typeof value.content === "string" && value.content.trim()) return value.content;
    if (Array.isArray(value.content)) {
      const text = value.content.map(part => part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string" ? (part as Record<string, unknown>).text : "").join("");
      if (text.trim()) return text;
    }
  }
  return undefined;
}

export function extractUserTurns(messages: unknown[]): Turn[] {
  return messages.flatMap(item => {
    if (!item || typeof item !== "object") return [];
    const value = item as Record<string, unknown>;
    if (value.role !== "user") return [];
    if (typeof value.content === "string" && value.content.trim()) return [{ role: "user" as const, content_utf8: value.content }];
    if (!Array.isArray(value.content)) return [];
    const content = value.content.map(part => part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string" ? (part as Record<string, unknown>).text : "").join("");
    return content.trim() ? [{ role: "user" as const, content_utf8: content }] : [];
  }).slice(-2);
}

export function captureScope(context: unknown, configured = "local-default-user"): string {
  const value = context && typeof context === "object" ? context as Record<string, unknown> : {};
  const identity = ["accountId", "userId", "senderId"].map(key => value[key]).find(item => typeof item === "string" && item.length) as string | undefined;
  const provider = typeof value.messageProvider === "string" ? value.messageProvider : typeof value.channelId === "string" ? value.channelId : "local";
  return identity ? `${provider}:${identity}` : configured;
}

export function turnKey(sessionKey: string, runId?: string, messageId?: string, content = ""): string {
  const marker = runId || messageId || createHash("sha256").update(wellFormedText(content)).digest("hex");
  return `${sessionKey}\0${marker}`;
}

export function latencyScenario(config: DreamConfig, sessionKey: string): string {
  const match = sessionKey.match(/(?:^|[-:])(PREHEAT|W_(?:NEW_SINGLE|NEW_MULTI|REUSE|REVISION_TRUE|ADDITIVE|NO_MEMORY|COLD_AFTER_RESTART|DENSE_LOCALITY)|R_(?:RELEVANT_WARM|RELEVANT_COLD|DENSE_HIDDEN_PREVIEW|NONE|REPEATED_TOPIC|MULTI_FACT))(?:[-:]|$)/i);
  return match?.[1].toUpperCase() ?? config.latency_scenario_id ?? "unspecified";
}

export function modelOverride(ref?: string): { provider: string; model: string } | undefined {
  if (!ref) return undefined;
  const separator = ref.indexOf("/");
  if (separator <= 0 || separator === ref.length - 1) return undefined;
  return { provider: ref.slice(0, separator), model: ref.slice(separator + 1) };
}

export function batchAbsorptionModel(
  config: Pick<DreamConfig, "model_mode" | "model" | "allowed_models">,
  records: ReadonlyArray<Pick<CaptureRecord, "model_ref">>,
): string | undefined {
  if (config.model_mode === "dedicated") return config.model;
  const observed = records.map(record => record.model_ref).find(Boolean);
  if (observed) return observed;
  return config.allowed_models?.length === 1 ? config.allowed_models[0] : undefined;
}

async function trace(config: DreamConfig, value: object): Promise<void> {
  if (!config.debug_trace || !config.evidence_path) return;
  assertMutableEvidencePath(config.evidence_path, config.evidence_run_id);
  await mkdir(dirname(config.evidence_path), { recursive: true });
  await appendFile(config.evidence_path, `${JSON.stringify(value)}\n`, "utf8");
}

export function assertMutableEvidencePath(path: string, runId?: string): void {
  if (typeof path !== "string" || !path) throw new Error("debug evidence_path is required");
  const parts = path.replace(/\\/g, "/").split("/").filter(Boolean);
  const lowered = parts.map(part => part.toLowerCase());
  if (lowered.includes("frozen")) throw new Error("frozen evidence artifacts are not writable");
  const liveIndex = lowered.lastIndexOf("live");
  if (liveIndex < 0 || liveIndex + 2 !== parts.length - 1 || lowered.at(-1) !== "events.jsonl") {
    throw new Error("debug evidence_path must be run-scoped as live/<run_id>/events.jsonl");
  }
  if (!parts[liveIndex + 1] || (runId !== undefined && parts[liveIndex + 1] !== runId)) {
    throw new Error("evidence_run_id does not match evidence_path");
  }
}

export function writerFormatRepairPrompt(raw: string, error: string): string {
  return `You repair JSON syntax and envelope formatting only. Return exactly one raw JSON object with no markdown. Preserve every semantic string value from the prior output byte-for-byte, including content_utf8, query_utf8, normalized_value, quote_utf8, IDs, and reason text. Do not add, remove, split, merge, summarize, or rewrite any proposition. If exact preservation is impossible, return the prior bytes unchanged.\nValidation error: ${error}\nPrior output:\n${raw}`;
}

export function writerFormatRepairable(parsed: Record<string, unknown>): boolean {
  return parsed.ok !== true && String(parsed.error ?? "") === "invalid_json";
}

export function legacyReaderEnabled(): boolean {
  return false;
}

export function registerDreamAgent(api: OpenClawPluginApi): void {
  const config = (api.pluginConfig ?? {}) as DreamConfig;
  if (config.debug_trace) assertMutableEvidencePath(config.evidence_path ?? "", config.evidence_run_id);
  const configuredMemoryWorkspace = config.memory_workspace ?? config.statement_store_workspace;
  const captureRoot = config.capture_workspace ?? (configuredMemoryWorkspace ? join(configuredMemoryWorkspace, "openclaw-capture-spool") : undefined);
  const captureStore = config.capture_enabled === false || !captureRoot ? undefined : new CaptureStore(captureRoot);
  const pending = new Map<string, Pending>();
  const inFlight = new Set<string>();
  const scheduled = new Set<string>();
  const childParents = new Map<string, { parentRunId?: string; requestedModel?: string }>();
  const mainAgentRecallOperations = new Map<string, MainAgentRecallOperation>();
  const mainAgentToolBindings = new Map<string, MainAgentRunScope>();
  const hostToolBindings = new Map<string, HostToolBinding>();
  const successfulMainAgentRecallCalls = new Set<string>();
  const runMemoryUseStates = new Map<string, RunMemoryUseState>();
  const captureIdsByRun = new Map<string, Set<string>>();
  let duplicateHookObservationCount = 0;
  let duplicateDreamSuppressedCount = 0;
  const backgroundScope = new AsyncResource("nollm-formation-background");
  const queue = (work: () => void) => { queueMicrotask(() => backgroundScope.runInAsyncScope(work)); };
  const recordHandler = (hook: string, startedAt: number, startedMonoNs: bigint, extra: object) => {
    const returnedAt = Date.now();
    const handlerDurationUs = durationUs(startedMonoNs, systemLatencyClock.monotonicNs());
    queue(() => { void trace(config, { status: "hook", hook, hook_observed_at: startedAt, hook_handler_returned_at: returnedAt, hook_handler_duration_us: handlerDurationUs, hook_handler_duration_ms: handlerDurationUs / 1_000, ...extra }); });
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
  const operationTtlMs = () => config.main_agent_operation_ttl_ms ?? 300000;
  const runIdentityKey = (sessionKey: string, runId: string): string => `${sessionKey}\0${runId}`;
  const runScope = (sessionKey: string, runId: string, context?: unknown): MainAgentRunScope => ({
    sessionKey, runId, scopeId: captureScope(context, config.capture_scope_id ?? "local-default-user"),
    workspaceId: configuredMemoryWorkspace ?? "",
  });
  const memoryUseState = (scope: MainAgentRunScope): RunMemoryUseState => {
    const key = runIdentityKey(scope.sessionKey, scope.runId);
    const existing = runMemoryUseStates.get(key);
    if (existing) {
      if (existing.scope.scopeId !== scope.scopeId || existing.scope.workspaceId !== scope.workspaceId) throw new Error("main-agent run scope changed");
      return existing;
    }
    const created: RunMemoryUseState = { scope, actions: new Set(), recalledStatementIds: new Set(), toolEvidenceIds: new Set(), sequence: 0, finalized: false };
    runMemoryUseStates.set(key, created);
    return created;
  };
  const roleMode = (state: RunMemoryUseState | undefined) =>
    state?.actions.has("recall") || state?.actions.has("expand") ? "memory_derived" as const
      : state?.actions.has("surface") ? "context_only" as const : "source" as const;
  const publishRunDirectives = async (state: RunMemoryUseState, epoch = Date.now()) => {
    if (!captureStore) return;
    const ids = captureIdsByRun.get(runIdentityKey(state.scope.sessionKey, state.scope.runId)) ?? new Set<string>();
    for (const captureId of ids) {
      await captureStore.publishDirective({
        captureId, mainRunIdentity: state.scope.runId, assistantRoleMode: roleMode(state),
        memoryToolActions: [...state.actions], selectedEntryId: state.selectedEntryId,
        recalledStatementIds: [...state.recalledStatementIds], toolEvidenceIds: [...state.toolEvidenceIds], directiveEpochMs: epoch,
        sequence: state.sequence, finalized: state.finalized,
      });
    }
  };
  const recordMemoryAction = async (binding: MainAgentRunScope, action: MemoryToolAction, details: Record<string, unknown> = {}) => {
    const state = memoryUseState(binding);
    state.actions.add(action);
    if (typeof details.entry_id === "string") state.selectedEntryId = details.entry_id;
    if (Array.isArray(details.statement_ids)) for (const id of details.statement_ids) if (typeof id === "string") state.recalledStatementIds.add(id);
    state.sequence += 1;
    await publishRunDirectives(state);
  };
  const atlasPolicy = (): Record<string, number> => ({
    max_regions_per_page: config.recall_atlas_max_regions ?? config.recall_surface_max_cells ?? 32,
    max_prompt_bytes: config.cartographer_max_prompt_bytes ?? 65536,
    max_depth: config.surface_max_order ?? 8,
    max_order: config.surface_max_order ?? 8,
    support_limit: 4,
  });
  const expireOperations = (now = Date.now()) => {
    for (const [operationId, operation] of mainAgentRecallOperations) {
      if (operation.expiresAt <= now) mainAgentRecallOperations.delete(operationId);
    }
  };
  const clearRunOperations = (sessionKey: string | undefined, runId: string | undefined) => {
    if (!sessionKey || !runId) return;
    for (const [operationId, operation] of mainAgentRecallOperations) {
      if (operation.scope.sessionKey === sessionKey && operation.scope.runId === runId) mainAgentRecallOperations.delete(operationId);
    }
  };
  const clearSessionOperations = (sessionKey: string | undefined) => {
    if (!sessionKey) return;
    for (const [operationId, operation] of mainAgentRecallOperations) {
      if (operation.scope.sessionKey === sessionKey) mainAgentRecallOperations.delete(operationId);
    }
  };
  api.on("before_tool_call", (event, ctx) => {
    if (!ctx.toolCallId || !ctx.sessionKey) return;
    const runId = ctx.runId ?? event.runId;
    if (!runId) return;
    const actualScope = captureScope(ctx, config.capture_scope_id ?? "local-default-user");
    if (actualScope !== (config.capture_scope_id ?? "local-default-user")) return;
    const binding = {
      sessionKey: ctx.sessionKey,
      runId,
      scopeId: actualScope,
      workspaceId: configuredMemoryWorkspace ?? "",
    };
    hostToolBindings.set(ctx.toolCallId, { ...binding, toolName: event.toolName, input: event.params, observedEpochMs: Date.now() });
    if (event.toolName === "nollm_memory") mainAgentToolBindings.set(ctx.toolCallId, binding);
  });
  api.on("after_tool_call", async (event, ctx) => {
    if (!ctx.toolCallId) return;
    const hostBinding = hostToolBindings.get(ctx.toolCallId);
    if (captureStore && hostBinding) {
      const raw = event as unknown as Record<string, unknown>;
      const context = ctx as unknown as Record<string, unknown>;
      const result = Object.hasOwn(raw, "result") ? raw.result : Object.hasOwn(raw, "output") ? raw.output
        : Object.hasOwn(raw, "content") ? raw.content : Object.hasOwn(raw, "error") ? { error: raw.error } : null;
      const published = await captureStore.publishToolEvidence({
        scopeKey: hostBinding.scopeId, workspaceKey: hostBinding.workspaceId || hostBinding.scopeId,
        sessionKey: hostBinding.sessionKey, mainRunIdentity: hostBinding.runId,
        toolCallId: ctx.toolCallId, toolName: hostBinding.toolName, input: hostBinding.input, result,
        succeeded: raw.success !== false && raw.error === undefined,
        visibility: raw.visibility === "internal" ? "internal" : "main_agent_visible",
        observedEpochMs: typeof raw.completedAt === "number" ? raw.completedAt : hostBinding.observedEpochMs,
        provider: typeof context.modelProviderId === "string" ? context.modelProviderId : undefined,
        model: typeof context.modelId === "string" ? context.modelId : undefined,
        hostVersion: "openclaw", pluginVersion: CAPTURE_PLUGIN_VERSION,
      });
      const state = memoryUseState(hostBinding);
      state.toolEvidenceIds.add(published.record.tool_evidence_id);
      state.sequence += 1;
      await publishRunDirectives(state, published.record.observed_epoch_ms);
    }
    hostToolBindings.delete(ctx.toolCallId);
    if (event.toolName !== "nollm_memory") return;
    const binding = mainAgentToolBindings.get(ctx.toolCallId);
    if (binding && successfulMainAgentRecallCalls.delete(ctx.toolCallId)) {
      await trace(config, {
        status: "completed", stage: "tool_recall_satisfied", session_key: binding.sessionKey,
        run_id: binding.runId, scope_id: binding.scopeId, workspace_id: binding.workspaceId,
        tool_call_id: ctx.toolCallId, hidden_child_calls: 0,
      });
    }
    mainAgentToolBindings.delete(ctx.toolCallId);
  });
  if (config.enabled !== false && config.main_agent_recall_enabled !== false && typeof api.registerTool === "function") {
    api.registerTool({
      name: "nollm_memory",
      label: "Nollm memory",
      description: "Inspect a routing-only Nollm map. Open a region when it has children, then select one entry and call recall, or call none. The Surface is not answer evidence; recalled content is returned only by recall or same-entry expand.",
      parameters: Type.Object({
        action: Type.Union([Type.Literal("surface"), Type.Literal("open_region"), Type.Literal("recall"), Type.Literal("expand"), Type.Literal("none")]),
        operation_id: Type.Optional(Type.String({ minLength: 1, maxLength: 128 })),
        region_id: Type.Optional(Type.String({ minLength: 1, maxLength: 256 })),
        entry_id: Type.Optional(Type.String({ minLength: 1, maxLength: 256 })),
        budget_option_id: Type.Optional(Type.Union([Type.Literal("default"), Type.Literal("expanded")])),
      }, { additionalProperties: false }),
      async execute(toolCallId: string, params: { action: "surface" | "open_region" | "recall" | "expand" | "none"; operation_id?: string; region_id?: string; entry_id?: string; budget_option_id?: "default" | "expanded" }) {
        const result = (value: unknown) => ({ content: [{ type: "text" as const, text: JSON.stringify(value) }], details: value });
        if (!configuredMemoryWorkspace || !config.python_executable || !config.nollm_repo_root) {
          return result({ status: "unavailable", reason: "Nollm memory workspace is not configured", legacy_reader: false });
        }
        const binding = mainAgentToolBindings.get(toolCallId);
        if (!binding) return result({ status: "run_scope_unavailable", legacy_reader: false });
        expireOperations();
        if (params.action === "surface") {
          if (params.region_id !== undefined || params.entry_id !== undefined || params.budget_option_id !== undefined) return result({ status: "invalid_parameters", legacy_reader: false });
          const operationId = `memory-${randomUUID()}`;
          const policy = atlasPolicy();
          const built = await bridge(config, {
            action: "build_main_agent_surface", memory_workspace: configuredMemoryWorkspace,
            operation_id: operationId, policy,
          });
          if (built.ok !== true || typeof built.core_state_sha256 !== "string" || typeof built.atlas_fingerprint !== "string" || typeof built.page_fingerprint !== "string" || !Array.isArray(built.entries) || !Array.isArray(built.regions) || typeof built.page !== "object" || built.page === null) return result({ ...built, legacy_reader: false });
          const entries = new Map<string, Record<string, unknown>>();
          for (const raw of built.entries) {
            if (typeof raw === "object" && raw !== null && typeof (raw as Record<string, unknown>).entry_id === "string") {
              entries.set((raw as Record<string, unknown>).entry_id as string, raw as Record<string, unknown>);
            }
          }
          const regions = new Map<string, string>();
          for (const raw of built.regions) if (typeof raw === "object" && raw !== null) {
            const item = raw as Record<string, unknown>;
            if (typeof item.region_id === "string" && typeof item.atlas_region_id === "string") regions.set(item.region_id, item.atlas_region_id);
          }
          const now = Date.now();
          reserveMainAgentOperationSlot(mainAgentRecallOperations, now);
          mainAgentRecallOperations.set(operationId, {
            scope: binding, createdAt: now, lastUsedAt: now, expiresAt: now + operationTtlMs(),
            coreStateSha256: built.core_state_sha256, atlasFingerprint: built.atlas_fingerprint,
            pageFingerprint: built.page_fingerprint, policy: built.policy as Record<string, number>, page: built.page as Record<string, unknown>, entries, regions, expanded: false,
          });
          await recordMemoryAction(binding, "surface");
          return result({
            schema_version: built.schema_version, status: built.status, operation_id: operationId,
            regions: (built.regions as Array<Record<string, unknown>>).map(({ atlas_region_id: _private, ...visible }) => visible), entry_count: built.entry_count, region_count: built.region_count,
            routing_text_chars: built.routing_text_chars, visible_json_utf8_bytes: built.visible_json_utf8_bytes,
            full_statement_body_count: built.full_statement_body_count, routing_only: true,
            answer_from_surface: false, single_entry_only: true,
            expires_at: now + operationTtlMs(), legacy_reader: false, hidden_child_calls: 0,
          });
        }
        if (!params.operation_id) return result({ status: "operation_missing", legacy_reader: false });
        const operation = mainAgentRecallOperations.get(params.operation_id);
        if (!operation) return result({ status: "operation_missing", legacy_reader: false });
        if (!sameMainAgentRun(operation.scope, binding)) return result({ status: "operation_scope_mismatch", legacy_reader: false });
        operation.lastUsedAt = Date.now();
        operation.expiresAt = operation.lastUsedAt + operationTtlMs();
        if (params.action === "open_region") {
          if (!params.region_id || params.entry_id !== undefined || params.budget_option_id !== undefined || operation.selectedEntryId) return result({ status: "invalid_parameters", legacy_reader: false });
          const atlasRegionId = operation.regions.get(params.region_id);
          if (!atlasRegionId) return result({ status: "region_unavailable", legacy_reader: false });
          const opened = await bridge(config, {
            action: "open_main_agent_region", memory_workspace: configuredMemoryWorkspace,
            operation_id: params.operation_id, parent_page: operation.page, atlas_region_id: atlasRegionId,
          });
          if (opened.ok !== true || typeof opened.page_fingerprint !== "string" || !Array.isArray(opened.entries) || !Array.isArray(opened.regions) || typeof opened.page !== "object" || opened.page === null) {
            if (opened.error !== "bridge_process_error" && opened.error !== "bridge_invalid_json") mainAgentRecallOperations.delete(params.operation_id);
            return result({ ...opened, legacy_reader: false });
          }
          operation.pageFingerprint = opened.page_fingerprint;
          operation.page = opened.page as Record<string, unknown>;
          operation.entries = new Map((opened.entries as Array<Record<string, unknown>>).map(item => [String(item.entry_id), item]));
          operation.regions = new Map((opened.regions as Array<Record<string, unknown>>).map(item => [String(item.region_id), String(item.atlas_region_id)]));
          await recordMemoryAction(binding, "open_region");
          return result({
            schema_version: opened.schema_version, status: opened.status, operation_id: params.operation_id,
            regions: (opened.regions as Array<Record<string, unknown>>).map(({ atlas_region_id: _private, ...visible }) => visible),
            entry_count: opened.entry_count, region_count: opened.region_count, depth: opened.depth,
            routing_text_chars: opened.routing_text_chars, visible_json_utf8_bytes: opened.visible_json_utf8_bytes,
            full_statement_body_count: opened.full_statement_body_count, routing_only: true, answer_from_surface: false,
            single_entry_only: true, expires_at: operation.expiresAt, legacy_reader: false, hidden_child_calls: 0,
          });
        }
        if (params.action === "none") {
          mainAgentRecallOperations.delete(params.operation_id);
          await recordMemoryAction(binding, "none");
          return result({ status: "none", operation_id: params.operation_id, legacy_reader: false });
        }
        let entryId = params.entry_id;
        let budgetOptionId: "default" | "expanded" = "default";
        if (params.action === "recall") {
          if (!entryId || !params.region_id || params.budget_option_id === "expanded") return result({ status: "invalid_parameters", legacy_reader: false });
          if (operation.selectedEntryId && operation.selectedEntryId !== entryId) return result({ status: "entry_locked", legacy_reader: false });
        } else {
          if (entryId !== undefined || params.region_id !== undefined || params.budget_option_id === "default" || !operation.selectedEntryId || operation.expanded) return result({ status: "invalid_expansion", legacy_reader: false });
          entryId = operation.selectedEntryId;
          budgetOptionId = "expanded";
        }
        const entry = operation.entries.get(entryId!);
        if (!entry) return result({ status: "entry_unavailable", legacy_reader: false });
        if (params.action === "recall" && entry.region_id !== params.region_id) return result({ status: "region_entry_mismatch", legacy_reader: false });
        const recalled = await bridge(config, {
          action: "recall_main_agent_locality", memory_workspace: configuredMemoryWorkspace,
          operation_id: params.operation_id, expected_core_state_sha256: operation.coreStateSha256,
          expected_atlas_fingerprint: operation.atlasFingerprint, expected_page_fingerprint: operation.pageFingerprint,
          policy: operation.policy, entry, budget_option_id: budgetOptionId, page: operation.page,
        });
        if (recalled.ok !== true) {
          if (!(["bridge_process_error", "bridge_invalid_json"] as unknown[]).includes(recalled.error)) {
            mainAgentRecallOperations.delete(params.operation_id);
          }
        } else {
          successfulMainAgentRecallCalls.add(toolCallId);
          if (params.action === "recall") {
            operation.selectedEntryId = entryId;
            operation.selectedRegionId = params.region_id;
          } else {
            operation.expanded = true;
            mainAgentRecallOperations.delete(params.operation_id);
          }
          const statementIds = Array.isArray(recalled.items)
            ? recalled.items.flatMap(item => item && typeof item === "object" && typeof (item as Record<string, unknown>).statement_id === "string" ? [(item as Record<string, unknown>).statement_id] : [])
            : [];
          await recordMemoryAction(binding, params.action, { entry_id: entryId, statement_ids: statementIds });
        }
        return result({ ...recalled, legacy_reader: false, hidden_child_calls: 0 });
      },
    });
  }
  const absorbCapturedBatch = async (batchId: string, records: CaptureRecord[], executionId: string): Promise<AbsorptionResult[]> => {
    const model = batchAbsorptionModel(config, records);
    if (!usableModel(model) || !config.python_executable || !config.nollm_repo_root || !configuredMemoryWorkspace || config.write_mode !== "statement-store") {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: "absorption configuration or model temporarily unavailable" }));
    }
    const requestIdBase = `cartography-${batchId}`;
    const providerKey = `${batchId}:${executionId}`;
    const directives = captureStore ? await Promise.all(records.map(record => captureStore.directive(record.capture_id))) : [];
    if (directives.length !== records.length || directives.some(item => item?.finalized !== true)) {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: "Capture absorption directive is not finalized" }));
    }
    const captures = records.map((record, index) => ({
      capture_id: record.capture_id,
      user_utf8: record.user_utf8,
      assistant_utf8: record.assistant_utf8,
      captured_epoch_ms: record.captured_epoch_ms,
      timezone_offset_minutes: record.reference_timezone_offset_minutes ?? 0,
      assistant_origin_kind: directives[index]!.assistant_role_mode === "memory_derived" ? "recalled_memory"
        : directives[index]!.assistant_role_mode === "context_only" ? "model_inference" : "assistant",
      memory_tool_actions: directives[index]!.memory_tool_actions,
      recalled_statement_ids: directives[index]!.recalled_statement_ids,
    }));
    const toolEvidenceIds = [...new Set(directives.flatMap(item => item!.tool_evidence_ids))].sort();
    const toolEvidence = captureStore ? await Promise.all(toolEvidenceIds.map(async id => {
      const item = await captureStore.readToolEvidence(id);
      return {
        tool_evidence_id: item.tool_evidence_id, tool_result_utf8: item.tool_result_utf8,
        observed_epoch_ms: item.observed_epoch_ms,
        source_capture_ids: records.filter((_record, index) => directives[index]!.tool_evidence_ids.includes(id)).map(record => record.capture_id).sort(),
      };
    })) : [];
    const contextRecords = captureStore
      ? await captureStore.contextBefore(records, config.writer_context_max_captures ?? 4, config.writer_context_max_chars ?? 6000)
      : [];
    const contextCaptures = contextRecords.map(record => ({
      capture_id: record.capture_id,
      user_utf8: record.user_utf8,
      assistant_utf8: record.assistant_utf8,
      captured_epoch_ms: record.captured_epoch_ms,
      timezone_offset_minutes: record.reference_timezone_offset_minutes ?? 0,
    }));
    const sourceGroupsByCapture = new Map(records.map(record => [record.capture_id, buildCaptureSourceWindowGroups(
      [record], config.writer_source_window_bytes ?? 12000,
      config.writer_source_group_bytes ?? 32000, config.writer_source_overlap_codepoints ?? 128,
    )]));
    if ([...sourceGroupsByCapture.values()].some(groups => !groups.length)) return records.map(record => ({ captureId: record.capture_id, status: "structural_invalid", error: "Capture has no source text" }));
    const priorStates = captureStore ? await Promise.all(records.map(record => captureStore.currentState(record.capture_id))) : [];
    const stateByCapture = new Map(records.map((record, index) => [record.capture_id, priorStates[index]]));
    const progress = records.map(record => {
      const state = stateByCapture.get(record.capture_id)!;
      const groups = sourceGroupsByCapture.get(record.capture_id)!;
      return {
        record, state, groups, groupIndex: state.continuation?.group_index ?? 0,
        continuationPass: state.continuation?.pass_index ?? 0,
        priorStatementIds: [...new Set(state.statement_ids ?? [])].sort(),
      };
    });
    if (progress.some(item => item.groupIndex >= item.groups.length)) return progress.map(item => ({
      captureId: item.record.capture_id, status: "incomplete_continuation" as const,
      statementIds: item.priorStatementIds, error: "Capture continuation cursor is outside its source groups",
      continuation: item.state.continuation,
    }));
    const sourceWindows = progress.flatMap(item => item.groups[item.groupIndex]);
    const unionPriorStatementIds = [...new Set(progress.flatMap(item => item.priorStatementIds))].sort();
    const priorContextResult = unionPriorStatementIds.length ? await bridge(config, {
      action: "read_statement_continuation_context", memory_workspace: configuredMemoryWorkspace,
      statement_ids: unionPriorStatementIds,
    }) : { ok: true, statements: [] };
    if (priorContextResult.ok !== true || !Array.isArray(priorContextResult.statements)) {
      return progress.map(item => ({ captureId: item.record.capture_id, status: "retryable_defer" as const, statementIds: item.priorStatementIds, error: "prior Statement continuation context is unavailable" }));
    }
    const priorContextById = new Map((priorContextResult.statements as Array<Record<string, unknown>>).map(item => [String(item.statement_id), item]));
    const continuationInput = { captures: progress.map(item => ({
      capture_id: item.record.capture_id, pass: item.continuationPass, group_index: item.groupIndex,
      prior_statements: item.priorStatementIds.map(id => priorContextById.get(id)).filter((value): value is Record<string, unknown> => value !== undefined),
    })).sort((left, right) => left.capture_id.localeCompare(right.capture_id)) };
    const continuationPass = Math.max(...progress.map(item => item.continuationPass));
    const requestId = `${requestIdBase}:progress:${sha256Text(JSON.stringify(continuationInput))}`;
    const memoryIdentity = await bridge(config, { action: "read_memory_evaluation_fingerprint", memory_workspace: configuredMemoryWorkspace });
    if (memoryIdentity.ok !== true || typeof memoryIdentity.current_memory_fingerprint !== "string") {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: "current memory fingerprint is unavailable" }));
    }
    const writerBuilt = await bridge(config, {
      action: "build_proposition_writer_prompt", request_id: requestId, captures, context_captures: contextCaptures,
      max_statements: config.max_statements ?? 8, source_windows: sourceWindows,
      continuation: continuationInput,
      tool_evidence: toolEvidence,
      current_memory_fingerprint: memoryIdentity.current_memory_fingerprint,
    });
    if (writerBuilt.ok !== true || typeof writerBuilt.prompt !== "string") {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: String(writerBuilt.message ?? writerBuilt.error ?? "Proposition Writer prompt failed") }));
    }
    const writerRun = await runDreamSubagentDetailed(api, config, writerBuilt.prompt, model, `${providerKey}:writer`);
    let writerAttempt = writerRun.attempt;
    let writerProviderCalls = 1;
    let writerProviderMs = writerAttempt?.providerMs ?? 0;
    if (!writerAttempt?.raw) {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: `Proposition Writer failed: ${writerRun.error ?? "empty response"}` }));
    }
    let writer = await bridge(config, {
      action: "parse_proposition_writer_result", request_id: requestId,
      raw_model_response: writerAttempt.raw, captures, context_captures: contextCaptures,
      source_windows: sourceWindows, tool_evidence: toolEvidence, continuation_pass: continuationPass, evaluation_id: writerBuilt.evaluation_id,
    });
    if (writer.ok !== true) {
      await trace(config, { status: "correction_required", stage: "proposition_writer_validation", batch_id: batchId, ...outputEvidence(writerAttempt.raw), ...writer });
      const validationError = String(writer.message ?? writer.error ?? "Proposition Writer validation failed");
      if (!writerFormatRepairable(writer)) {
        return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: `Proposition Writer semantic validation failed: ${validationError}` }));
      }
      const correction = await runDreamSubagentDetailed(
        api, config,
        writerFormatRepairPrompt(writerAttempt.raw, validationError),
        model, `${providerKey}:writer-correction`,
      );
      writerProviderCalls += 1;
      writerProviderMs += correction.attempt?.providerMs ?? 0;
      writerAttempt = correction.attempt;
      if (!writerAttempt?.raw) {
        return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: `Proposition Writer correction failed: ${correction.error ?? "empty response"}` }));
      }
      writer = await bridge(config, {
        action: "parse_proposition_writer_result", request_id: requestId,
        raw_model_response: writerAttempt.raw, captures, context_captures: contextCaptures,
        source_windows: sourceWindows, tool_evidence: toolEvidence, continuation_pass: continuationPass, evaluation_id: writerBuilt.evaluation_id,
      });
      if (writer.ok !== true) {
        return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: String(writer.message ?? writer.error ?? "Proposition Writer correction validation failed") }));
      }
    }
    const contextFingerprint = sha256Text(JSON.stringify(contextCaptures.map(item => [item.capture_id, item.captured_epoch_ms])));
    const evaluationFor = (item: typeof progress[number], complete = false): CaptureEvaluationIdentity => ({
      writer_schema: String(writerBuilt.schema_version), prompt_version: String(writerBuilt.prompt_version),
      context_fingerprint: contextFingerprint, current_memory_fingerprint: String(memoryIdentity.current_memory_fingerprint),
      source_coverage: sha256Text(JSON.stringify(complete ? item.groups.flat() : item.groups[item.groupIndex])), evaluation_epoch_ms: Date.now(),
    });
    const ranges = (groups: typeof progress[number]["groups"], predicate: (index: number) => boolean) => groups.flatMap((group, index) => predicate(index) ? group.map(window => ({ capture_id: window.capture_id, role: window.role, start: window.start, end: window.end })) : []);
    const nextContinuation = (item: typeof progress[number], nextGroup: number, nextPass: number): CaptureContinuation => ({
      group_index: nextGroup, pass_index: nextPass, total_groups: item.groups.length,
      covered_ranges: ranges(item.groups, index => index <= item.groupIndex),
      uncovered_ranges: ranges(item.groups, index => index > item.groupIndex),
      prior_propositions: item.priorStatementIds.map(id => priorContextById.get(id)).filter((value): value is Record<string, unknown> => value !== undefined) as CaptureContinuation["prior_propositions"],
    });
    const captureProgress = new Map(
      (Array.isArray(writer.capture_progress) ? writer.capture_progress : []).flatMap(value =>
        value && typeof value === "object" && typeof (value as Record<string, unknown>).capture_id === "string"
          ? [[(value as Record<string, unknown>).capture_id as string, value as Record<string, unknown>] as const]
          : []),
    );
    const progressStatus = (item: typeof progress[number]): string => String(captureProgress.get(item.record.capture_id)?.status ?? "retryable_defer");
    const completeWithoutDelta = (item: typeof progress[number]): AbsorptionResult => item.groupIndex + 1 < item.groups.length
      ? { captureId: item.record.capture_id, status: "incomplete_continuation", statementIds: item.priorStatementIds, evaluation: evaluationFor(item), continuation: nextContinuation(item, item.groupIndex + 1, 0) }
      : item.priorStatementIds.length
        ? { captureId: item.record.capture_id, status: "admitted", statementIds: item.priorStatementIds, evaluation: evaluationFor(item, true) }
        : { captureId: item.record.capture_id, status: "evaluated_no_new_propositions", statementIds: [], evaluation: evaluationFor(item, true) };
    if (writer.outcome === "retryable_defer") return progress.map(item => ({ captureId: item.record.capture_id, status: "retryable_defer" as const, statementIds: item.priorStatementIds, error: String(writer.reason_text ?? "Proposition Writer retryable defer"), evaluation: evaluationFor(item) }));
    if (writer.outcome === "zero_new_propositions") {
      return progress.map(item => progressStatus(item) === "retryable_defer"
        ? { captureId: item.record.capture_id, status: "retryable_defer" as const, statementIds: item.priorStatementIds, error: "Capture requested retry", evaluation: evaluationFor(item) }
        : completeWithoutDelta(item));
    }
    if (writer.outcome === "incomplete_continuation" && (!Array.isArray(writer.propositions) || writer.propositions.length === 0)) {
      return progress.map(item => progressStatus(item) === "retryable_defer"
        ? { captureId: item.record.capture_id, status: "retryable_defer" as const, statementIds: item.priorStatementIds, error: "Capture requested retry", evaluation: evaluationFor(item) }
        : progressStatus(item) === "continue"
          ? { captureId: item.record.capture_id, status: "incomplete_continuation" as const, statementIds: item.priorStatementIds, evaluation: evaluationFor(item), continuation: nextContinuation(item, item.groupIndex, item.continuationPass + 1) }
          : completeWithoutDelta(item));
    }

    let cartography = await bridge(config, {
      action: "build_field_cartographer_prompt", request_id: requestId,
      writer_result: writer, memory_workspace: configuredMemoryWorkspace, turn: 1,
    });
    if (cartography.ok !== true || cartography.status !== "cartographer_decision" || typeof cartography.prompt !== "string") {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: String(cartography.message ?? cartography.error ?? cartography.status ?? "Field Cartographer prompt failed") }));
    }
    const cartographerSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
    const cartographerRaw: string[] = [];
    const cartographerResolved: Record<string, string>[] = [];
    let cartographerProviderMs = 0;
    let cartographerTurns = 0;
    let cartographerError: string | undefined;
    try {
      while (cartographerTurns < (config.cartographer_max_turns ?? 4)) {
        const turn = Number(cartography.turn);
        const run = await runDreamSubagentInSession(
          api, config, cartography.prompt as string, model, `${providerKey}:cartographer:${turn}`, cartographerSessionKey,
        );
        cartographerTurns += 1;
        cartographerProviderMs += run.attempt?.providerMs ?? 0;
        if (!run.attempt?.raw) { cartographerError = run.error ?? "empty response"; break; }
        cartographerRaw.push(run.attempt.raw);
        cartographerResolved.push(run.attempt.resolved);
        cartography = await bridge(config, {
          action: "advance_field_cartographer", request_id: requestId,
          raw_model_response: run.attempt.raw, writer_result: writer,
          page: cartography.page, memory_workspace: configuredMemoryWorkspace, turn,
        });
        if (cartography.ok !== true) { cartographerError = String(cartography.message ?? cartography.error ?? "invalid Cartographer output"); break; }
        if (cartography.status === "complete") break;
        if (cartography.status !== "cartographer_decision" || typeof cartography.prompt !== "string") {
          cartographerError = String(cartography.status ?? "invalid Cartographer continuation"); break;
        }
      }
    } finally {
      if (!config.persist_subagent_transcripts) {
        try { await api.runtime.subagent.deleteSession({ sessionKey: cartographerSessionKey, deleteTranscript: true }); } catch { /* diagnostic cleanup is best effort */ }
      }
    }
    if (cartographerError || cartography.status !== "complete") {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: `Field Cartographer failed: ${cartographerError ?? "turn budget exhausted"}` }));
    }
    if (cartography.outcome === "defer") {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: String(cartography.reason_text ?? "Field Cartographer deferred") }));
    }
    let applied = await bridge(config, {
      action: "apply_field_cartography_result", request_id: requestId,
      cartography_result: cartography, writer_result: writer, captures: [...captures, ...contextCaptures],
      memory_workspace: configuredMemoryWorkspace,
    });
    if (applied.ok !== true || !Array.isArray(applied.outcomes)) {
      return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: String(applied.message ?? applied.error ?? "Field Cartographer apply failed") }));
    }
    let outcomes = applied.outcomes as Array<Record<string, unknown>>;
    for (const item of outcomes.filter(value => value.outcome === "revision_confirmation_required")) {
      const confirmationBuilt = await bridge(config, { action: "build_revision_confirmation_prompt", provisional_revision: item.provisional_revision });
      if (confirmationBuilt.ok !== true || typeof confirmationBuilt.prompt !== "string") continue;
      const confirmationRun = await runDreamSubagent(api, config, confirmationBuilt.prompt, model, `${providerKey}:revision-confirmation:${String(item.statement_id ?? "unknown")}`);
      if (!confirmationRun?.raw || typeof item.statement_id !== "string") continue;
      const confirmation = await bridge(config, { action: "parse_revision_confirmation", raw_model_response: confirmationRun.raw, provisional_revision: item.provisional_revision });
      if (confirmation.ok !== true || !confirmation.confirmation) continue;
      const revisionApplied = await bridge(config, {
        action: "apply_field_cartography_result", request_id: requestId,
        cartography_result: cartography, writer_result: writer, captures: [...captures, ...contextCaptures],
        memory_workspace: configuredMemoryWorkspace,
        revision_confirmations: { [item.statement_id]: confirmation.confirmation },
        only_statement_ids: [item.statement_id],
      });
      if (revisionApplied.ok === true && Array.isArray(revisionApplied.outcomes)) {
        const replacement = (revisionApplied.outcomes as Array<Record<string, unknown>>)[0];
        outcomes = outcomes.map(value => value.statement_id === item.statement_id ? replacement : value);
      }
    }
    const errors = outcomes.filter(item => item.outcome === "error");
    const deferred = outcomes.filter(item => item.outcome === "defer" || item.outcome === "revision_confirmation_required");
    await trace(config, {
      status: errors.length || deferred.length ? "partial" : "completed", stage: "absorption_batch",
      batch_id: batchId, capture_count: records.length, statement_count: outcomes.length,
      proposition_writer_provider_calls: writerProviderCalls, proposition_writer_provider_ms: writerProviderMs,
      writer_context_capture_count: contextCaptures.length,
      writer_context_chars: contextCaptures.reduce((total, item) => total + item.user_utf8.length + item.assistant_utf8.length, 0),
      cartographer_sessions: 1, cartographer_turns: cartographerTurns,
      cartographer_provider_ms: cartographerProviderMs, common_one_writer_call: writerProviderCalls === 1,
      atlas_fingerprint: cartography.atlas_fingerprint, writer_raw: outputEvidence(writerAttempt.raw),
      writer_resolved: writerAttempt.resolved, cartographer_raw: cartographerRaw.map(outputEvidence),
      cartographer_resolved: cartographerResolved, validated_plans: applied.plans, durable_outcomes: outcomes,
    });
    return records.map(record => {
      const item = progress.find(value => value.record.capture_id === record.capture_id)!;
      const priorStatementIds = item.priorStatementIds;
      const evaluation = evaluationFor(item);
      if (progressStatus(item) === "retryable_defer") return { captureId: record.capture_id, status: "retryable_defer", statementIds: priorStatementIds, error: "Capture requested retry", evaluation };
      const related = outcomes.filter(item => Array.isArray(item.source_capture_ids) && item.source_capture_ids.includes(record.capture_id));
      if (related.some(item => item.outcome === "error")) return { captureId: record.capture_id, status: "retryable_defer", statementIds: priorStatementIds, error: "one or more independent Admissions failed", evaluation };
      if (related.some(item => item.outcome === "revision_confirmation_required")) return { captureId: record.capture_id, status: "retryable_defer", statementIds: priorStatementIds, error: "revision confirmation remains retryable", evaluation };
      if (related.some(item => item.outcome !== "applied")) return { captureId: record.capture_id, status: "retryable_defer", statementIds: priorStatementIds, error: "one or more Capture Statements deferred", evaluation };
      const statementIds = [...new Set([...priorStatementIds, ...related.flatMap(item => typeof item.statement_id === "string" ? [item.statement_id] : [])])].sort();
      const reopenVerified = related.every(item => item.durable_commit && (item.durable_commit as Record<string, unknown>).reopen_verified === true);
      if (!reopenVerified && related.length) return { captureId: record.capture_id, status: "retryable_defer" as const, statementIds, error: "Admission reopen verification failed", evaluation };
      if (progressStatus(item) === "continue") return { captureId: record.capture_id, status: "incomplete_continuation" as const, statementIds, evaluation, continuation: nextContinuation(item, item.groupIndex, item.continuationPass + 1) };
      if (item.groupIndex + 1 < item.groups.length) return { captureId: record.capture_id, status: "incomplete_continuation" as const, statementIds, evaluation, continuation: nextContinuation(item, item.groupIndex + 1, 0) };
      return statementIds.length
        ? { captureId: record.capture_id, status: "admitted" as const, statementIds, evaluation: evaluationFor(item, true) }
        : { captureId: record.capture_id, status: "evaluated_no_new_propositions" as const, statementIds: [], evaluation: evaluationFor(item, true) };
    });
  };
  const reevaluationNeeded = async (record: CaptureRecord, state: CaptureStateEvent): Promise<boolean> => {
    const evaluation = state.evaluation;
    if (!captureStore || !evaluation || state.status === "evaluated_no_new_propositions_legacy") return true;
    if (evaluation.writer_schema !== "nollm_openclaw_content_neutral_proposition_writer_v4" ||
        evaluation.prompt_version !== "proposition-writer-v4-content-neutral-evidence-continuation") return true;
    const contextRecords = await captureStore.contextBefore(
      [record], config.writer_context_max_captures ?? 4, config.writer_context_max_chars ?? 6000,
    );
    const contextFingerprint = sha256Text(JSON.stringify(contextRecords.map(item => [item.capture_id, item.captured_epoch_ms])));
    if (evaluation.context_fingerprint !== contextFingerprint) return true;
    const groups = buildCaptureSourceWindowGroups(
      [record], config.writer_source_window_bytes ?? 12000,
      config.writer_source_group_bytes ?? 32000, config.writer_source_overlap_codepoints ?? 128,
    );
    if (evaluation.source_coverage !== sha256Text(JSON.stringify(groups.flat()))) return true;
    if (!configuredMemoryWorkspace) return false;
    const identity = await bridge(config, { action: "read_memory_evaluation_fingerprint", memory_workspace: configuredMemoryWorkspace });
    return identity.ok === true && typeof identity.current_memory_fingerprint === "string" &&
      identity.current_memory_fingerprint !== evaluation.current_memory_fingerprint;
  };
  const absorptionWorker = captureStore && config.absorption_enabled !== false ? new AbsorptionWorker(captureStore, {
    batchMaxCaptures: config.absorption_batch_max_captures ?? 4,
    batchMaxChars: config.absorption_batch_max_chars ?? 24000,
    staleClaimMs: config.absorption_stale_claim_ms ?? 300000,
    retryBackoffMs: config.absorption_retry_backoff_ms ?? 1000,
    directiveFinalizationMs: config.absorption_directive_finalization_ms ?? 30000,
    continuationPassesPerRun: config.writer_max_continuation_passes ?? 16,
    reevaluationNeeded,
  }, absorbCapturedBatch) : undefined;
  let absorptionTimer: NodeJS.Timeout | undefined;
  let absorptionServiceRunning = false;
  const scheduleAbsorption = () => {
    if (!absorptionWorker || !absorptionServiceRunning || absorptionTimer) return;
    absorptionTimer = setTimeout(() => {
      absorptionTimer = undefined;
      void (async () => {
        if (!absorptionServiceRunning) return;
        const scan = captureStore ? await captureStore.scanRecords() : { diagnostics: [] };
        if (scan.diagnostics.length) await trace(config, { status: "warning", stage: "capture_integrity", corrupt_capture_count: scan.diagnostics.length, files: scan.diagnostics.map(item => item.file) });
        await absorptionWorker.runOnce();
        scheduleAbsorption();
      })();
    }, config.absorption_max_wait_ms ?? 250);
    absorptionTimer.unref?.();
  };
  api.registerService?.({
    id: "nollm-durable-capture-absorption",
    start: () => { absorptionServiceRunning = true; scheduleAbsorption(); },
    stop: () => {
      absorptionServiceRunning = false;
      if (absorptionTimer) clearTimeout(absorptionTimer);
      absorptionTimer = undefined;
      mainAgentRecallOperations.clear();
      mainAgentToolBindings.clear();
      successfulMainAgentRecallCalls.clear();
      runMemoryUseStates.clear();
      captureIdsByRun.clear();
    },
  });
  const publishCapture = async (sessionKey: string, runId: string | undefined, user: string | undefined, assistant: string, context: unknown, model?: string, finalized = false) => {
    if (!captureStore || !user?.trim() || !assistant.trim()) return undefined;
    const scope = runId ? runScope(sessionKey, runId, context) : undefined;
    const receipt = await captureStore.publish({
      scopeKey: captureScope(context, config.capture_scope_id ?? "local-default-user"), sessionKey,
      workspaceKey: configuredMemoryWorkspace ?? captureRoot!,
      turnIdentity: runId ?? createHash("sha256").update(`${user}\0${assistant}`).digest("hex"),
      userUtf8: user, assistantUtf8: assistant, modelRef: configuredModel(model),
      profileId: config.capture_scope_id ?? "local-default-user", mainRunIdentity: runId ?? sessionKey,
      endpointKind: "visible_assistant_delivery", pluginVersion: "0.16.0",
    });
    if (scope) {
      const key = runIdentityKey(sessionKey, runId!);
      const ids = captureIdsByRun.get(key) ?? new Set<string>(); ids.add(receipt.record.capture_id); captureIdsByRun.set(key, ids);
      const state = memoryUseState(scope);
      if (finalized && !state.finalized) { state.finalized = true; state.sequence += 1; }
      await publishRunDirectives(state, receipt.record.captured_epoch_ms + state.sequence);
    }
    await trace(config, { status: "captured", stage: "capture", capture_id: receipt.record.capture_id, capture_content_sha256: receipt.record.content_sha256, capture_publish_ms: receipt.publish_ms, replayed: receipt.replayed, raw_capture_preserved: true, directive_finalized: finalized, provider_calls: 0, bridge_calls: 0, core_calls: 0 });
    scheduleAbsorption();
    return receipt;
  };
  api.on("agent_turn_prepare", async (event, ctx) => {
    const observedAt = Date.now();
    const operationStartedMonoNs = systemLatencyClock.monotonicNs();
    const memoryWorkspace = config.memory_workspace ?? config.statement_store_workspace;
    if (config.enabled === false || ctx.agentId === "nollm-dream-agent" || !ctx.sessionKey || !event.prompt.trim()) return;
    let pendingInjection = "";
    if (captureStore && config.pending_fallback_enabled !== false) {
      const pendingStartedMonoNs = systemLatencyClock.monotonicNs();
      const recent = await captureStore.renderPending(captureScope(ctx, config.capture_scope_id ?? "local-default-user"), {
        maxCaptures: config.pending_fallback_max_captures ?? 4,
        maxChars: config.pending_fallback_max_chars ?? 6000,
        maxAgeMs: config.pending_fallback_max_age_ms ?? 604800000,
      });
      if (recent.injection) {
        await trace(config, { status: "completed", stage: "pending_fallback", capture_ids: recent.captureIds, rendered_chars: recent.chars, local_ms: durationMs(pendingStartedMonoNs, systemLatencyClock.monotonicNs()), hidden_provider_calls: 0 });
        pendingInjection = recent.injection;
      }
    }
    const combinedContext = (admitted = ""): { appendContext: string } | undefined => {
      const parts = [admitted, pendingInjection].filter(Boolean);
      if (!parts.length) return undefined;
      return { appendContext: parts.join("\n\n") };
    };
    if (!memoryWorkspace || !config.python_executable || !config.nollm_repo_root) return combinedContext();
    // The old Reader remains a Lab baseline only; active Recall uses the main-agent tool.
    if (!legacyReaderEnabled()) return combinedContext();
    const model = configuredModel(ctx.modelProviderId && ctx.modelId ? `${ctx.modelProviderId}/${ctx.modelId}` : undefined);
    if (!usableModel(model)) return combinedContext();
    const requestId = `recall-${createHash("sha256").update(`${ctx.sessionKey}\0${ctx.runId ?? event.prompt}`).digest("hex")}`;
    if ((config.recall_hidden_call_budget ?? 1) === 1) {
      const built = await bridge(config, {
        action: "build_fast_recall_prompt", request_id: requestId, query: event.prompt, memory_workspace: memoryWorkspace,
        max_entries: config.recall_surface_max_cells ?? 32, max_statements: config.max_statements ?? 8,
        max_chars: config.max_total_chars ?? 8192,
      });
      if (built.ok !== true) { await trace(config, { status: "error", stage: "fast_recall_build", request_id: requestId, ...built }); return; }
      if (built.status === "complete_none") {
        await trace(config, { status: "completed_none", stage: "fast_recall", request_id: requestId, hidden_provider_calls: 0, operation_timing: { total_operation_ms: durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()) } });
        return combinedContext();
      }
      if (built.status === "complete_inject" && typeof built.injection === "string") {
        if (ctx.runId) await recordMemoryAction(runScope(ctx.sessionKey, ctx.runId, ctx), "recall", { entry_id: built.selected_entry, statement_ids: built.statement_ids });
        await trace(config, { status: "completed", stage: "fast_recall", request_id: requestId, hidden_provider_calls: 0, selected_entry: built.selected_entry, statement_ids: built.statement_ids, operation_timing: { total_operation_ms: durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()) } });
        return combinedContext(built.injection);
      }
      if (built.status !== "entry_decision" || typeof built.prompt !== "string" || !Array.isArray(built.entries)) return combinedContext();
      const selected = await runHiddenAgent(built.prompt, model!, `${requestId}:single-entry`);
      if (!selected.raw) { await trace(config, { status: "defer", stage: "fast_recall_agent", request_id: requestId, hidden_provider_calls: 1, error: selected.error }); return combinedContext(); }
      const applied = await bridge(config, {
        action: "apply_fast_recall_selection", request_id: requestId, raw_model_response: selected.raw,
        entries: built.entries, memory_workspace: memoryWorkspace, max_statements: config.max_statements ?? 8,
        max_chars: config.max_total_chars ?? 8192,
      });
      const totalOperationMs = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
      if (applied.ok !== true || applied.outcome === "none") {
        await trace(config, { status: applied.ok === true ? "completed_none" : "error", stage: "fast_recall", request_id: requestId, hidden_provider_calls: 1, operation_timing: { total_operation_ms: totalOperationMs }, ...selected.resolved, ...applied });
        return combinedContext();
      }
      if (applied.outcome === "inject" && typeof applied.injection === "string") {
        if (ctx.runId) await recordMemoryAction(runScope(ctx.sessionKey, ctx.runId, ctx), "recall", { entry_id: applied.selected_entry, statement_ids: applied.statement_ids });
        await trace(config, { status: "completed", stage: "fast_recall", request_id: requestId, hidden_provider_calls: 1, selected_entry: applied.selected_entry, statement_ids: applied.statement_ids, selected_paths: applied.selected_paths, operation_timing: { total_operation_ms: totalOperationMs }, ...selected.resolved });
        return combinedContext(applied.injection);
      }
      return combinedContext();
    }
    const timing: Record<string, number | string | boolean | null> = {
      surface_build_ms: 0, surface_order_count: 0, surface_projection_count: 0,
      surface_page_count: 0, physical_entry_resolution_ms: 0, recall_core_ms: 0,
      physical_entry_model_call_skipped: false, recall_agent_ms: 0,
      surface_traversal_provider_ms: 0, traversal_correction_ms: 0,
      recall_selection_provider_ms: 0, injection_render_us: 0,
      model_call_count: 0, invalid_decision_count: 0, correction_attempt_count: 0,
      correction_success: false, provider_timeout_stage: null,
      total_operation_ms: 0, timeout_stage: null,
    };
    let stageStartedMonoNs = systemLatencyClock.monotonicNs();
    let built = await bridge(config, { action: "build_recall_prompt", request_id: requestId, query: event.prompt, memory_workspace: memoryWorkspace, surface_budget: surfaceBudget(config, "recall") });
    timing.surface_build_ms = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
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
      stageStartedMonoNs = systemLatencyClock.monotonicNs();
      let step = await runHiddenAgent(current.prompt as string, model!, `${requestId}:surface:${traversal}`);
      timing.model_call_count = Number(timing.model_call_count) + 1;
      const surfaceProviderMs = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
      timing.surface_traversal_provider_ms = Number(timing.surface_traversal_provider_ms) + surfaceProviderMs;
      timing.recall_agent_ms = Number(timing.recall_agent_ms) + surfaceProviderMs;
      if (!step.raw) { timing.timeout_stage = "recall_surface_agent"; timing.provider_timeout_stage = "recall_surface_agent"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await trace(config, { status: "defer", stage: "recall_surface_agent", request_id: requestId, error: step.error, hook_observed_at: observedAt, operation_timing: timing }); return; }
      stageStartedMonoNs = systemLatencyClock.monotonicNs();
      let advanced = await bridge(config, { action: "advance_recall_traversal", query: event.prompt, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: memoryWorkspace });
      while (traversalRetryable(advanced)) {
        timing.invalid_decision_count = Number(timing.invalid_decision_count) + 1;
        if (Number(timing.correction_attempt_count) >= TRAVERSAL_CORRECTION_MAX_ATTEMPTS) break;
        timing.correction_attempt_count = Number(timing.correction_attempt_count) + 1;
        stageStartedMonoNs = systemLatencyClock.monotonicNs();
        step = await runHiddenAgent(traversalCorrectionPrompt(current.prompt as string, step.raw, advanced, Number(timing.correction_attempt_count)), model!, `${requestId}:surface:${traversal}:correction:${timing.correction_attempt_count}`);
        timing.model_call_count = Number(timing.model_call_count) + 1;
        const correctionProviderMs = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
        timing.traversal_correction_ms = Number(timing.traversal_correction_ms) + correctionProviderMs;
        timing.recall_agent_ms = Number(timing.recall_agent_ms) + correctionProviderMs;
        if (!step.raw) { timing.timeout_stage = "recall_traversal_correction"; timing.provider_timeout_stage = "recall_traversal_correction"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await trace(config, { status: "defer", stage: "recall_traversal_correction", request_id: requestId, error: step.error, operation_timing: timing }); return; }
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
      timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
      const injectionReadyEpochMs = Date.now();
      pendingRecallLatencyByRun.set(`${ctx.sessionKey}\0${ctx.runId ?? ""}`, { requestId, mainRunId: ctx.runId, queryPrepareEpochMs: observedAt, injectionReadyEpochMs, outcome: "none" });
      await appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, ctx.sessionKey), event_type: "recall_terminal", recall_request_id: requestId, session_key_sha256: sha256Text(ctx.sessionKey), main_run_id: ctx.runId, query_hash: sha256Text(event.prompt), query_prepare_epoch_ms: observedAt, injection_ready_epoch_ms: injectionReadyEpochMs, query_to_none_terminal_ms: timing.total_operation_ms, recall_outcome: "none", selected_statement_count: 0, hidden_injection_created: false, operation_timing: timing });
      await trace(config, { status: "completed_none", stage: "recall", request_id: requestId, entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing });
      return;
    }
    if (built.ok !== true || built.status !== "recall_decision" || typeof built.prompt !== "string") {
      timing.timeout_stage = "recall_surface_terminal"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
      await trace(config, { status: "defer", stage: "recall_surface_terminal", request_id: requestId, bridge_status: built.status, bridge_error: built.error, bridge_code: built.code, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing });
      return;
    }
    stageStartedMonoNs = systemLatencyClock.monotonicNs();
    const selected = await runHiddenAgent(built.prompt, model!, `${requestId}:recall-selection`);
    timing.model_call_count = Number(timing.model_call_count) + 1;
    const selectionProviderMs = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
    timing.recall_selection_provider_ms = selectionProviderMs;
    timing.recall_agent_ms = Number(timing.recall_agent_ms) + selectionProviderMs;
    if (!selected.raw) { timing.timeout_stage = "recall_agent"; timing.provider_timeout_stage = "recall_agent"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await trace(config, { status: "defer", stage: "recall_agent", request_id: requestId, error: selected.error, hook_observed_at: observedAt, operation_timing: timing }); return; }
    const injectionRenderStartedMonoNs = systemLatencyClock.monotonicNs();
    const rendered = await bridge(config, { action: "render_recall_injection", raw_model_response: selected.raw, candidates: built.candidates });
    timing.injection_render_us = durationUs(injectionRenderStartedMonoNs, systemLatencyClock.monotonicNs());
    timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
    if (rendered.ok === true && rendered.outcome === "none") {
      const injectionReadyEpochMs = Date.now();
      pendingRecallLatencyByRun.set(`${ctx.sessionKey}\0${ctx.runId ?? ""}`, { requestId, mainRunId: ctx.runId, queryPrepareEpochMs: observedAt, injectionReadyEpochMs, outcome: "none" });
      await appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, ctx.sessionKey), event_type: "recall_terminal", recall_request_id: requestId, session_key_sha256: sha256Text(ctx.sessionKey), main_run_id: ctx.runId, query_hash: sha256Text(event.prompt), query_prepare_epoch_ms: observedAt, injection_ready_epoch_ms: injectionReadyEpochMs, query_to_none_terminal_ms: timing.total_operation_ms, recall_outcome: "none", selected_statement_count: 0, hidden_injection_created: false, operation_timing: timing, ...selected.resolved });
      await trace(config, { status: "completed_none", stage: "recall", request_id: requestId, entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing, ...selected.resolved });
      return;
    }
    if (rendered.ok !== true || rendered.outcome !== "inject" || typeof rendered.injection !== "string") return;
    const injectionReadyEpochMs = Date.now();
    const injectionHash = sha256Text(rendered.injection);
    pendingRecallLatencyByRun.set(`${ctx.sessionKey}\0${ctx.runId ?? ""}`, { requestId, mainRunId: ctx.runId, queryPrepareEpochMs: observedAt, injectionReadyEpochMs, outcome: "inject", injectionHash });
    await appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, ctx.sessionKey), event_type: "recall_terminal", recall_request_id: requestId, session_key_sha256: sha256Text(ctx.sessionKey), main_run_id: ctx.runId, query_hash: sha256Text(event.prompt), query_prepare_epoch_ms: observedAt, injection_ready_epoch_ms: injectionReadyEpochMs, query_to_injection_ready_ms: timing.total_operation_ms, recall_outcome: "inject", selected_statement_ids: rendered.statement_ids, selected_statement_count: Array.isArray(rendered.statement_ids) ? rendered.statement_ids.length : 0, injection_hash: injectionHash, hidden_injection_created: true, operation_timing: timing, ...selected.resolved });
    await trace(config, { status: "completed", stage: "recall", request_id: requestId, selected_statement_ids: rendered.statement_ids, selected_paths: selectedRecallPaths(built.candidates, rendered.statement_ids), entry_cell: built.entry_cell, core_recall: built.core_recall, surface_path: surfacePath, visible_message_count: 0, operation_timing: timing, ...selected.resolved });
    if (ctx.runId) await recordMemoryAction(runScope(ctx.sessionKey, ctx.runId, ctx), "recall", { statement_ids: rendered.statement_ids });
    return { appendContext: rendered.injection };
  });
  api.on("before_agent_run", (event, ctx) => {
    const observedAt = Date.now();
    const observedMonoNs = systemLatencyClock.monotonicNs();
    if (config.enabled === false || !ctx.sessionKey || ctx.agentId === "nollm-dream-agent") { recordHandler("before_agent_run", observedAt, observedMonoNs, {}); return; }
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    current.runId = ctx.runId ?? current.runId;
    if (ctx.modelProviderId && ctx.modelId) current.resolvedModel = `${ctx.modelProviderId}/${ctx.modelId}`;
    pending.set(ctx.sessionKey, current);
    recordHandler("before_agent_run", observedAt, observedMonoNs, { session_key: ctx.sessionKey, run_id: ctx.runId, model_provider_id: ctx.modelProviderId, model_id: ctx.modelId });
  });
  api.on("message_received", (event, ctx) => {
    const observedAt = Date.now();
    const observedMonoNs = systemLatencyClock.monotonicNs();
    if (config.enabled === false || !ctx.sessionKey || typeof event.content !== "string" || !event.content.trim()) return;
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    const content = wellFormedText(event.content);
    const identity = event.messageId || `${event.runId ?? ctx.runId ?? ""}:${createHash("sha256").update(content).digest("hex")}`;
    if (!current.users.some(turn => turn.identity === identity)) current.users = [...current.users, { role: "user", content_utf8: content, identity } as UserObservation].slice(-2);
    else duplicateHookObservationCount += 1;
    current.runId = event.runId ?? ctx.runId ?? current.runId;
    pending.set(ctx.sessionKey, current);
    recordHandler("message_received", observedAt, observedMonoNs, { session_key: ctx.sessionKey, run_id: current.runId, message_id: event.messageId });
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
    const formationPromptBuildStartedMonoNs = systemLatencyClock.monotonicNs();
    const built = await bridge(config, { action: "build_dream_prompt", request, prompt_version: config.prompt_version ?? "dream-json-p1" });
    const formationPromptBuildUs = durationUs(formationPromptBuildStartedMonoNs, systemLatencyClock.monotonicNs());
    if (built.ok !== true || typeof built.prompt !== "string") { await trace(config, { status: "error", stage: "build_prompt", ...built }); return; }
    inFlight.add(sessionKey);
    const dreamStartedAt = Date.now();
    const backgroundQueueWaitMs = durationMs(candidate.observedMonoNs, systemLatencyClock.monotonicNs());
    try {
      const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
      const override = config.model_mode === "dedicated" ? modelOverride(model) : undefined;
      childParents.set(childSessionKey, { parentRunId: candidate.runId ?? current.runId, requestedModel: model });
      const formationProviderStartedMonoNs = systemLatencyClock.monotonicNs();
      const spawned = await api.runtime.subagent.run({
        sessionKey: childSessionKey, message: built.prompt,
        ...(override ?? {}),
        lightContext: true, deliver: false, idempotencyKey,
      });
      const turnId = turnCorrelationId(sessionKey, candidate.runId ?? current.runId, assistant);
      await appendLatencyEvent(config, COMMIT_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, sessionKey), event_type: "formation_started", turn_correlation_id: turnId, formation_request_id: requestId, formation_run_id: spawned.runId, session_key_sha256: sha256Text(sessionKey), main_run_id: candidate.runId ?? current.runId, source_hook: sourceHook, turn_visible_source_valid: sourceHook === "message_sent", turn_visible_epoch_ms: observedAt, background_started_epoch_ms: dreamStartedAt, background_queue_wait_ms: backgroundQueueWaitMs, formation_prompt_build_us: formationPromptBuildUs, visible_assistant_message_hash: sha256Text(assistant), requested_model: model });
      await trace(config, { status: "started", request_id: requestId, turn_key_sha256: createHash("sha256").update(key).digest("hex"), session_key: sessionKey, parent_run_id: candidate.runId ?? current.runId, child_session_key: childSessionKey, run_id: spawned.runId, requested_model: model, model_mode: config.model_mode ?? "inherit", prompt_version: built.prompt_version, prompt_sha256: built.prompt_sha256, schema_sha256: built.schema_sha256, source_hook: sourceHook, trigger_phase: phase, hook_observed_at: observedAt, background_scheduled_at: dreamStartedAt, prompt_build_started_at: dreamStartedAt, subagent_started_at: Date.now(), deliver: false, material: request.material, duplicate_hook_observation_count: duplicateHookObservationCount, duplicate_dream_suppressed_count: duplicateDreamSuppressedCount });
      void completeDream(api, config, sessionKey, childSessionKey, spawned.runId, request, built, inFlight, dreamStartedAt, formationProviderStartedMonoNs, formationPromptBuildUs, idempotencyKey, turnId, observedAt, sourceHook, model);
    } catch (error) {
      inFlight.delete(sessionKey);
      await trace(config, { status: "error", stage: "spawn", request_id: requestId, error: String(error), trigger_phase: phase });
    }
  };
  api.on("message_sent", async (event, ctx) => {
    const observedAt = Date.now();
    const observedMonoNs = systemLatencyClock.monotonicNs();
    const sessionKey = ctx.sessionKey ?? event.sessionKey;
    if (!event.success || !sessionKey || !event.content.trim()) { recordHandler("message_sent", observedAt, observedMonoNs, { success: event.success }); return; }
    const current = pending.get(sessionKey); const runId = event.runId ?? ctx.runId ?? current?.runId;
    const exactAssistant = wellFormedText(event.content);
    const exactUser = current?.users.at(-1)?.content_utf8;
    await publishCapture(sessionKey, runId, exactUser, exactAssistant, ctx, current?.resolvedModel);
    const recallKey = `${sessionKey}\0${runId ?? ""}`;
    const recall = pendingRecallLatencyByRun.get(recallKey);
    if (recall) {
      pendingRecallLatencyByRun.delete(recallKey);
      queue(() => { void appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, sessionKey), event_type: "visible_answer", recall_request_id: recall.requestId, session_key_sha256: sha256Text(sessionKey), main_run_id: runId, recall_outcome: recall.outcome, injection_hash: recall.injectionHash, main_message_sent_epoch_ms: observedAt, query_to_visible_answer_ms: observedAt - recall.queryPrepareEpochMs, injection_to_visible_answer_ms: observedAt - recall.injectionReadyEpochMs, visible_answer_correlated: true, visible_answer_hash: sha256Text(event.content), visible_message_count: 1 }); });
    } else {
      for (const [key, unmatched] of pendingRecallLatencyByRun) {
        if (!key.startsWith(`${sessionKey}\0`)) continue;
        pendingRecallLatencyByRun.delete(key);
        queue(() => { void appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, sessionKey), event_type: "visible_answer", recall_request_id: unmatched.requestId, session_key_sha256: sha256Text(sessionKey), main_run_id: runId, expected_main_run_id: unmatched.mainRunId, recall_outcome: unmatched.outcome, main_message_sent_epoch_ms: observedAt, visible_answer_correlated: false, visible_answer_correlation_unavailable: true, correlation_failure: "main_run_id_mismatch", visible_message_count: 1 }); });
      }
    }
    recordHandler("message_sent", observedAt, observedMonoNs, { session_key: sessionKey, run_id: runId, trigger_phase: "AFTER_DELIVERY", success: true, legacy_formation_enabled: false });
  });
  api.on("agent_end", async (event, ctx) => {
    const observedAt = Date.now();
    const observedMonoNs = systemLatencyClock.monotonicNs();
    if (!event.success || !ctx.sessionKey || ctx.agentId === "nollm-dream-agent") return;
    const assistant = extractAssistantTextExact(event.messages);
    if (!assistant) return;
    const model = ctx.modelProviderId && ctx.modelId ? `${ctx.modelProviderId}/${ctx.modelId}` : undefined;
    const content = wellFormedText(assistant);
    const runId = event.runId ?? ctx.runId;
    const exactUsers = extractUserTurns(event.messages);
    await publishCapture(ctx.sessionKey, runId, exactUsers.at(-1)?.content_utf8, content, ctx, model, true);
    const recallKey = `${ctx.sessionKey}\0${runId ?? ""}`;
    const recall = pendingRecallLatencyByRun.get(recallKey);
    if (recall) {
      pendingRecallLatencyByRun.delete(recallKey);
      queue(() => { void appendLatencyEvent(config, RECALL_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, ctx.sessionKey!), event_type: "visible_answer", recall_request_id: recall.requestId, session_key_sha256: sha256Text(ctx.sessionKey!), main_run_id: runId, recall_outcome: recall.outcome, agent_end_epoch_ms: observedAt, visible_answer_correlated: false, visible_answer_correlation_unavailable: true, correlation_failure: "message_sent_not_observed", visible_message_count: 0 }); });
    }
    recordHandler("agent_end", observedAt, observedMonoNs, { session_key: ctx.sessionKey, run_id: runId, trigger_phase: "AFTER_TURN", success: true, legacy_formation_enabled: false });
    queue(() => {
      clearRunOperations(ctx.sessionKey, runId);
      if (runId) {
        const key = runIdentityKey(ctx.sessionKey!, runId);
        const timer = setTimeout(() => {
          runMemoryUseStates.delete(key);
          captureIdsByRun.delete(key);
        }, operationTtlMs());
        timer.unref?.();
      }
    });
  });
  api.on("session_end", (_event, ctx) => {
    clearSessionOperations(ctx.sessionKey);
    for (const key of runMemoryUseStates.keys()) if (ctx.sessionKey && key.startsWith(`${ctx.sessionKey}\0`)) runMemoryUseStates.delete(key);
    for (const key of captureIdsByRun.keys()) if (ctx.sessionKey && key.startsWith(`${ctx.sessionKey}\0`)) captureIdsByRun.delete(key);
  });
  api.on("gateway_stop", () => {
    mainAgentRecallOperations.clear();
    mainAgentToolBindings.clear();
    hostToolBindings.clear();
    successfulMainAgentRecallCalls.clear();
    runMemoryUseStates.clear();
    captureIdsByRun.clear();
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

async function completeDream(api: OpenClawPluginApi, config: DreamConfig, parentSession: string, childSession: string, runId: string, request: object, built: Record<string, unknown>, inFlight: Set<string>, startedAt: number, providerStartedMonoNs: bigint, formationPromptBuildUs: number, stableId: string, turnId: string, turnVisibleEpochMs: number, sourceHook: "message_sent" | "agent_end", model?: string): Promise<void> {
  let formationProviderTotalMs = 0;
  let formationParseUs = 0;
  let formationModelCallCount = 1;
  try {
    const waited = await api.runtime.subagent.waitForRun({ runId, timeoutMs: config.timeout_ms ?? 120000 });
    formationProviderTotalMs += durationMs(providerStartedMonoNs, systemLatencyClock.monotonicNs());
    if (waited.status !== "ok") { const completedAt = Date.now(); await trace(config, { status: waited.status, stage: "subagent", run_id: runId, error: waited.error, dream_completed_at: completedAt, dream_latency_ms: completedAt - startedAt, visible_message_count: 0 }); return; }
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSession, limit: 20 });
    const raw = extractAssistantText(session.messages);
    const resolved = extractResolvedModel(session.messages);
    if (!raw) { await trace(config, { status: "error", stage: "empty_output", run_id: runId, dream_completed_at: Date.now(), ...resolved, visible_message_count: 0 }); return; }
    let parseStartedMonoNs = systemLatencyClock.monotonicNs();
    let parsed = await parseDreamAttempt(config, request, raw, `dream-result-${stableId}`, "initial", runId, parentSession, startedAt, resolved, built.prompt_version);
    formationParseUs += durationUs(parseStartedMonoNs, systemLatencyClock.monotonicNs());
    if (formationRetryable(parsed)) {
      const repaired = await runFormatRepair(api, config, raw, String(parsed.error ?? "invalid_json"), model, stableId);
      if (repaired) {
        formationProviderTotalMs += repaired.providerMs;
        formationModelCallCount += 1;
        parseStartedMonoNs = systemLatencyClock.monotonicNs();
        parsed = await parseDreamAttempt(config, request, repaired.raw, `dream-result-${stableId}`, "format_repair", repaired.runId, parentSession, startedAt, repaired.resolved, "dream-format-repair-v1");
        formationParseUs += durationUs(parseStartedMonoNs, systemLatencyClock.monotonicNs());
      }
    }
    for (const version of ["dream-json-p1", "dream-json-p2"]) {
      if (!formationRetryable(parsed)) break;
      const retry = await runFullDreamRetry(api, config, request, version, model, stableId);
      if (retry) {
        formationProviderTotalMs += retry.providerMs;
        formationModelCallCount += 1;
        parseStartedMonoNs = systemLatencyClock.monotonicNs();
        parsed = await parseDreamAttempt(config, request, retry.raw, `dream-result-${stableId}`, version, retry.runId, parentSession, startedAt, retry.resolved, version);
        formationParseUs += durationUs(parseStartedMonoNs, systemLatencyClock.monotonicNs());
      }
    }
    const formationCompletedEpochMs = Date.now();
    const statements = Array.isArray(parsed.statements) ? parsed.statements as unknown[] : [];
    const formationLocalTotalMs = (formationPromptBuildUs + formationParseUs) / 1_000;
    await appendLatencyEvent(config, COMMIT_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, parentSession), event_type: "formation_completed", turn_correlation_id: turnId, formation_run_id: runId, source_hook: sourceHook, turn_visible_source_valid: sourceHook === "message_sent", turn_visible_epoch_ms: turnVisibleEpochMs, formation_completed_epoch_ms: formationCompletedEpochMs, formation_prompt_build_us: formationPromptBuildUs, formation_provider_total_ms: formationProviderTotalMs, formation_parse_us: formationParseUs, formation_local_total_ms: formationLocalTotalMs, turn_to_formation_complete_ms: formationCompletedEpochMs - turnVisibleEpochMs, formation_model_call_count: formationModelCallCount, formation_statement_count: statements.length, formation_terminal_status: parsed.ok === true ? "completed" : "error", resolved_provider: resolved.resolved_provider, resolved_model: resolved.resolved_model });
    if (shouldApplyPlacement(config, parsed, model)) {
      for (const [statementIndex, statement] of statements.entries()) await completePlacement(api, config, parentSession, statement, model!, stableId, { turnId, turnVisibleEpochMs, turnVisibleSourceValid: sourceHook === "message_sent", statementIndex, statementCount: statements.length, formationProviderTotalMs, formationLocalTotalMs, deprecatedCumulativeFormationMs: Date.now() - startedAt });
    }
  } catch (error) {
    await trace(config, { status: "error", stage: "completion", run_id: runId, dream_completed_at: Date.now(), error: String(error), visible_message_count: 0 });
  } finally {
    inFlight.delete(parentSession);
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey: childSession, deleteTranscript: true }); } catch { /* diagnostic cleanup is best effort */ } }
  }
}

type DreamAttempt = { raw: string; runId: string; resolved: Record<string, string>; providerMs: number };
type DreamRunResult = { attempt?: DreamAttempt; error?: string };

function outputEvidence(raw: string): Record<string, unknown> {
  return {
    raw_visible_output: raw, raw_visible_output_truncated: false,
    raw_visible_output_chars: raw.length, raw_visible_output_sha256: createHash("sha256").update(raw).digest("hex"),
    raw_visible_output_utf8_bytes: Buffer.byteLength(raw, "utf8"),
    raw_visible_output_line_count: raw.length === 0 ? 0 : raw.split(/\r?\n/).length,
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
  return (await runDreamSubagentDetailed(api, config, prompt, model, idempotencyKey)).attempt;
}

async function runDreamSubagentDetailed(api: OpenClawPluginApi, config: DreamConfig, prompt: string, model: string | undefined, idempotencyKey: string): Promise<DreamRunResult> {
  const sessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
  const override = config.model_mode === "dedicated" && model ? modelOverride(model) : undefined;
  const providerStartedMonoNs = systemLatencyClock.monotonicNs();
  try {
    const spawned = await api.runtime.subagent.run({ sessionKey, message: prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey });
    const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
    if (waited.status !== "ok") return { error: String(waited.error ?? waited.status) };
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey, limit: 20 });
    const raw = extractAssistantText(session.messages);
    return raw
      ? { attempt: { raw, runId: spawned.runId, resolved: extractResolvedModel(session.messages), providerMs: durationMs(providerStartedMonoNs, systemLatencyClock.monotonicNs()) } }
      : { error: "completed run had no assistant output" };
  } catch (error) {
    return { error: String(error) };
  } finally {
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey, deleteTranscript: true }); } catch { /* diagnostic cleanup is best effort */ } }
  }
}

async function runDreamSubagentInSession(
  api: OpenClawPluginApi,
  config: DreamConfig,
  prompt: string,
  model: string | undefined,
  idempotencyKey: string,
  sessionKey: string,
): Promise<DreamRunResult> {
  const override = config.model_mode === "dedicated" && model ? modelOverride(model) : undefined;
  const providerStartedMonoNs = systemLatencyClock.monotonicNs();
  try {
    const spawned = await api.runtime.subagent.run({ sessionKey, message: prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey });
    const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
    if (waited.status !== "ok") return { error: String(waited.error ?? waited.status) };
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey, limit: 20 });
    const raw = extractAssistantText(session.messages);
    return raw
      ? { attempt: { raw, runId: spawned.runId, resolved: extractResolvedModel(session.messages), providerMs: durationMs(providerStartedMonoNs, systemLatencyClock.monotonicNs()) } }
      : { error: "completed run had no assistant output" };
  } catch (error) {
    return { error: String(error) };
  }
}

type PlacementLatencyContext = { turnId: string; turnVisibleEpochMs: number; turnVisibleSourceValid: boolean; statementIndex: number; statementCount: number; formationProviderTotalMs: number; formationLocalTotalMs: number; deprecatedCumulativeFormationMs: number };

async function completePlacement(api: OpenClawPluginApi, config: DreamConfig, sessionKey: string, statement: unknown, model: string, stableId: string, context: PlacementLatencyContext): Promise<void> {
  const operationStartedMonoNs = systemLatencyClock.monotonicNs();
  const statementStartedEpochMs = Date.now();
  const timing: Record<string, number | string | boolean | null> = {
    formation_ms: context.deprecatedCumulativeFormationMs, formation_ms_deprecated: true,
    formation_provider_total_ms: context.formationProviderTotalMs, formation_local_total_ms: context.formationLocalTotalMs,
    statement_start_offset_ms: statementStartedEpochMs - context.turnVisibleEpochMs,
    statement_persist_us: 0, statement_persist_ms: 0, surface_build_ms: 0,
    surface_order_count: 0, surface_projection_count: 0, surface_page_count: 0,
    placement_prompt_build_ms: 0, placement_subagent_ms: 0, placement_json_repair_ms: 0,
    physical_entry_resolution_ms: 0, physical_entry_model_call_skipped: false,
    decision_validation_us: 0, decision_validation_ms: 0, core_apply_us: 0, placement_apply_ms: 0,
    handle_bind_us: 0, handle_bind_ms: 0, durable_readback_us: 0,
    model_call_count: 0, invalid_decision_count: 0, correction_attempt_count: 0,
    correction_success: false, provider_timeout_stage: null,
    revision_confirmation_count: 0, revision_confirmation_ms: 0,
    revision_confirmation_outcome: null, revision_redecision_count: 0,
    revision_redecision_ms: 0, revision_target_blacklisted: false,
    total_operation_ms: 0, timeout_stage: null,
  };
  const statementId = statement && typeof statement === "object" && typeof (statement as Record<string, unknown>).statement_id === "string" ? (statement as Record<string, unknown>).statement_id : "unknown";
  const requestId = `placement-${createHash("sha256").update(`${stableId}\0${statementId}`).digest("hex")}`;
  const recordPlacementTerminal = async (finalOutcome: "defer" | "error", terminalReason: string, error?: unknown): Promise<void> => {
    await appendLatencyEvent(config, COMMIT_LATENCY_SCHEMA, {
      scenario_id: latencyScenario(config, sessionKey), event_type: "placement_terminal",
      turn_correlation_id: context.turnId, turn_visible_source_valid: context.turnVisibleSourceValid,
      placement_request_id: requestId, statement_id: statementId, statement_index: context.statementIndex,
      statement_count: context.statementCount, statement_start_epoch_ms: statementStartedEpochMs,
      statement_start_offset_ms: timing.statement_start_offset_ms, final_outcome: finalOutcome,
      terminal_reason: terminalReason, error: error === undefined ? undefined : String(error),
      placement_provider_total_ms: timing.placement_subagent_ms,
      placement_local_total_ms: Number(timing.total_operation_ms) - Number(timing.placement_subagent_ms),
      operation_timing: timing,
    });
  };
  let stageStartedMonoNs = systemLatencyClock.monotonicNs();
  let built = await bridge(config, { action: "build_placement_prompt", request_id: requestId, statement, memory_workspace: config.memory_workspace ?? config.statement_store_workspace, surface_budget: surfaceBudget(config, "placement") });
  timing.surface_build_ms = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
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
    stageStartedMonoNs = systemLatencyClock.monotonicNs();
    let step = await runDreamSubagent(api, config, current.prompt as string, model, `${requestId}:surface:${traversal}`);
    timing.model_call_count = Number(timing.model_call_count) + 1;
    timing.placement_subagent_ms = Number(timing.placement_subagent_ms) + durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
    if (!step?.raw) { timing.timeout_stage = "placement_surface_agent"; timing.provider_timeout_stage = "placement_surface_agent"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await recordPlacementTerminal("defer", "placement_surface_agent"); await trace(config, { status: "defer", stage: "placement_surface_agent", request_id: requestId, operation_timing: timing }); return; }
    stageStartedMonoNs = systemLatencyClock.monotonicNs();
    let advanced = await bridge(config, { action: "advance_placement_traversal", statement, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: config.memory_workspace ?? config.statement_store_workspace });
    while (traversalRetryable(advanced)) {
      timing.invalid_decision_count = Number(timing.invalid_decision_count) + 1;
      if (Number(timing.correction_attempt_count) >= TRAVERSAL_CORRECTION_MAX_ATTEMPTS) break;
      timing.correction_attempt_count = Number(timing.correction_attempt_count) + 1;
      stageStartedMonoNs = systemLatencyClock.monotonicNs();
      step = await runDreamSubagent(api, config, traversalCorrectionPrompt(current.prompt as string, step.raw, advanced, Number(timing.correction_attempt_count)), model, `${requestId}:surface:${traversal}:correction:${timing.correction_attempt_count}`);
      timing.model_call_count = Number(timing.model_call_count) + 1;
      timing.placement_subagent_ms = Number(timing.placement_subagent_ms) + durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
      if (!step?.raw) { timing.timeout_stage = "placement_traversal_correction"; timing.provider_timeout_stage = "placement_traversal_correction"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await recordPlacementTerminal("defer", "placement_traversal_correction"); await trace(config, { status: "defer", stage: "placement_traversal_correction", request_id: requestId, operation_timing: timing }); return; }
      advanced = await bridge(config, { action: "advance_placement_traversal", statement, traversal_state: current.traversal_state, raw_model_response: step.raw, memory_workspace: config.memory_workspace ?? config.statement_store_workspace });
      if (advanced.ok === true) timing.correction_success = true;
    }
    built = advanced;
    const bridgeMs = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
    timing.placement_prompt_build_ms = Number(timing.placement_prompt_build_ms) + bridgeMs;
    const accessTiming = built.operation_timing && typeof built.operation_timing === "object" ? built.operation_timing as Record<string, unknown> : {};
    if (typeof accessTiming.physical_entry_resolution_ms === "number") timing.physical_entry_resolution_ms = accessTiming.physical_entry_resolution_ms;
    if (typeof accessTiming.physical_entry_model_call_skipped === "boolean") timing.physical_entry_model_call_skipped = accessTiming.physical_entry_model_call_skipped;
    traversal += 1;
  }
  if (built.ok !== true || built.status !== "placement_decision" || typeof built.prompt !== "string") { timing.timeout_stage = "placement_prompt"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await recordPlacementTerminal("defer", "placement_prompt", built.error); await trace(config, { status: "defer", stage: "placement_prompt", request_id: requestId, surface_path: surfacePath, operation_timing: timing, ...built }); return; }
  const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
  const override = config.model_mode === "dedicated" ? modelOverride(model) : undefined;
  try {
    stageStartedMonoNs = systemLatencyClock.monotonicNs();
    const spawned = await api.runtime.subagent.run({ sessionKey: childSessionKey, message: built.prompt, ...(override ?? {}), lightContext: true, deliver: false, idempotencyKey: `${requestId}:agent` });
    const waited = await api.runtime.subagent.waitForRun({ runId: spawned.runId, timeoutMs: config.timeout_ms ?? 120000 });
    timing.placement_subagent_ms = Number(timing.placement_subagent_ms) + durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
    timing.model_call_count = Number(timing.model_call_count) + 1;
    if (waited.status !== "ok") { timing.timeout_stage = "placement_agent"; timing.provider_timeout_stage = "placement_agent"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await recordPlacementTerminal("defer", "placement_agent", waited.error ?? waited.status); await trace(config, { status: "defer", stage: "placement_agent", request_id: requestId, error: waited.error ?? waited.status, operation_timing: timing }); return; }
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSessionKey, limit: 20 });
    const raw = extractAssistantText(session.messages);
    if (!raw) { timing.timeout_stage = "placement_agent"; timing.provider_timeout_stage = "placement_agent"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs()); await recordPlacementTerminal("defer", "placement_agent", "empty_output"); await trace(config, { status: "defer", stage: "placement_agent", request_id: requestId, error: "empty_output", operation_timing: timing }); return; }
    stageStartedMonoNs = systemLatencyClock.monotonicNs();
    let applied = await applyPlacementAttempt(config, requestId, raw, statement, built.selected_entry);
    timing.placement_apply_ms = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
    let attemptKind = "initial";
    if (placementRetryable(applied)) {
      stageStartedMonoNs = systemLatencyClock.monotonicNs();
      const repaired = await runFormatRepair(api, config, raw, String(applied.error ?? "invalid_json"), model, `${requestId}:format-repair`);
      if (repaired) timing.model_call_count = Number(timing.model_call_count) + 1;
      timing.placement_json_repair_ms = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
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
    if (applied.ok === true && applied.outcome === "revision_confirmation_required") {
      const provisional = applied.provisional_revision;
      const confirmationBuilt = await bridge(config, { action: "build_revision_confirmation_prompt", provisional_revision: provisional });
      if (confirmationBuilt.ok !== true || typeof confirmationBuilt.prompt !== "string") {
        timing.timeout_stage = "revision_confirmation_prompt";
        timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
        await recordPlacementTerminal("defer", "revision_confirmation_prompt", confirmationBuilt.error);
        await trace(config, { status: "defer", stage: "revision_confirmation_prompt", request_id: requestId, surface_path: surfacePath, operation_timing: timing, ...confirmationBuilt });
        return;
      }
      stageStartedMonoNs = systemLatencyClock.monotonicNs();
      const confirmationAttempt = await runDreamSubagent(api, config, confirmationBuilt.prompt, model, `${requestId}:revision-confirmation`);
      timing.revision_confirmation_count = 1;
      timing.model_call_count = Number(timing.model_call_count) + 1;
      timing.revision_confirmation_ms = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
      if (!confirmationAttempt?.raw) {
        timing.timeout_stage = "revision_confirmation_agent";
        timing.provider_timeout_stage = "revision_confirmation_agent";
        timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
        await recordPlacementTerminal("defer", "revision_confirmation_agent");
        await trace(config, { status: "defer", stage: "revision_confirmation_agent", request_id: requestId, provisional_revision: provisional, operation_timing: timing });
        return;
      }
      const parsedConfirmation = await bridge(config, { action: "parse_revision_confirmation", raw_model_response: confirmationAttempt.raw, provisional_revision: provisional });
      if (parsedConfirmation.ok !== true || typeof parsedConfirmation.confirmation !== "object" || parsedConfirmation.confirmation === null) {
        timing.revision_confirmation_outcome = "invalid";
        timing.timeout_stage = "revision_confirmation_parse";
        timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
        await recordPlacementTerminal("defer", "revision_confirmation_parse", parsedConfirmation.error);
        await trace(config, { status: "defer", stage: "revision_confirmation_parse", request_id: requestId, provisional_revision: provisional, operation_timing: timing, ...parsedConfirmation });
        return;
      }
      const confirmation = parsedConfirmation.confirmation as Record<string, unknown>;
      timing.revision_confirmation_outcome = String(confirmation.outcome ?? "invalid");
      if (confirmation.outcome === "confirm_revision") {
        applied = await applyPlacementAttempt(config, requestId, raw, statement, built.selected_entry, confirmation);
        attemptKind = "confirmed_revision";
      } else if (confirmation.outcome === "reject_revision") {
        const redecisionBuilt = await bridge(config, { action: "build_revision_redecision_prompt", original_prompt: built.prompt, provisional_revision: provisional, confirmation });
        if (redecisionBuilt.ok !== true || typeof redecisionBuilt.prompt !== "string" || !Array.isArray(redecisionBuilt.excluded_revision_targets)) {
          timing.timeout_stage = "revision_redecision_prompt";
          timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
          await recordPlacementTerminal("defer", "revision_redecision_prompt", redecisionBuilt.error);
          await trace(config, { status: "defer", stage: "revision_redecision_prompt", request_id: requestId, operation_timing: timing, ...redecisionBuilt });
          return;
        }
        timing.revision_target_blacklisted = true;
        stageStartedMonoNs = systemLatencyClock.monotonicNs();
        const redecisionAttempt = await runDreamSubagent(api, config, redecisionBuilt.prompt, model, `${requestId}:revision-redecision`);
        timing.revision_redecision_count = 1;
        timing.model_call_count = Number(timing.model_call_count) + 1;
        timing.revision_redecision_ms = durationMs(stageStartedMonoNs, systemLatencyClock.monotonicNs());
        if (!redecisionAttempt?.raw) {
          timing.timeout_stage = "revision_redecision_agent";
          timing.provider_timeout_stage = "revision_redecision_agent";
          timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
          await recordPlacementTerminal("defer", "revision_redecision_agent");
          await trace(config, { status: "defer", stage: "revision_redecision_agent", request_id: requestId, operation_timing: timing });
          return;
        }
        applied = await applyPlacementAttempt(config, requestId, redecisionAttempt.raw, statement, built.selected_entry, undefined, redecisionBuilt.excluded_revision_targets);
        attemptKind = "revision_redecision";
        if (applied.ok === true && applied.outcome === "revision_confirmation_required") {
          applied = { ok: true, outcome: "defer", reason: "revision_confirmation_call_consumed", core_write_count: 0 };
        }
      } else {
        applied = { ok: true, outcome: "defer", reason: "revision_confirmation_deferred", core_write_count: 0 };
      }
    }
    const accessTiming = applied.operation_timing && typeof applied.operation_timing === "object" ? applied.operation_timing as Record<string, number> : {};
    for (const key of ["statement_persist_us", "statement_persist_ms", "decision_validation_us", "decision_validation_ms", "core_apply_us", "placement_apply_ms", "handle_bind_us", "handle_bind_ms", "durable_readback_us"]) if (typeof accessTiming[key] === "number") timing[key] = accessTiming[key];
    timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
    if (applied.ok !== true) timing.timeout_stage = "placement_apply";
    const placementStatus = applied.ok !== true ? "error" : applied.outcome === "applied" ? "completed" : "defer";
    const durableCommit = applied.durable_commit && typeof applied.durable_commit === "object" ? applied.durable_commit as Record<string, unknown> : undefined;
    const statementDurableEpochMs = placementStatus === "completed" && durableCommit?.verified === true ? Date.now() : undefined;
    await appendLatencyEvent(config, COMMIT_LATENCY_SCHEMA, { scenario_id: latencyScenario(config, sessionKey), event_type: "placement_terminal", turn_correlation_id: context.turnId, turn_visible_source_valid: context.turnVisibleSourceValid, placement_request_id: requestId, statement_id: statementId, statement_index: context.statementIndex, statement_count: context.statementCount, statement_start_epoch_ms: statementStartedEpochMs, statement_start_offset_ms: timing.statement_start_offset_ms, statement_durable_epoch_ms: statementDurableEpochMs, statement_to_durable_ms: statementDurableEpochMs === undefined ? undefined : timing.total_operation_ms, turn_to_statement_durable_ms: statementDurableEpochMs === undefined || !context.turnVisibleSourceValid ? undefined : statementDurableEpochMs - context.turnVisibleEpochMs, placement_provider_total_ms: timing.placement_subagent_ms, placement_local_total_ms: Number(timing.total_operation_ms) - Number(timing.placement_subagent_ms), final_action: applied.action, final_outcome: applied.outcome, terminal_reason: applied.reason, durable_commit: durableCommit, operation_timing: timing, resolved_provider: extractResolvedModel(session.messages).resolved_provider, resolved_model: extractResolvedModel(session.messages).resolved_model });
    await trace(config, { status: placementStatus, stage: "placement_apply", placement_attempt: attemptKind, request_id: requestId, surface_path: surfacePath, visible_message_count: 0, ...applied, operation_timing: timing, ...extractResolvedModel(session.messages) });
  } catch (error) {
    timing.timeout_stage = "placement"; timing.total_operation_ms = durationMs(operationStartedMonoNs, systemLatencyClock.monotonicNs());
    await recordPlacementTerminal("error", "placement", error);
    await trace(config, { status: "error", stage: "placement", request_id: requestId, error: String(error), operation_timing: timing });
  } finally {
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey: childSessionKey, deleteTranscript: true }); } catch { /* best effort */ } }
  }
}

async function applyPlacementAttempt(config: DreamConfig, requestId: string, raw: string, statement: unknown, selectedEntry: unknown, revisionConfirmation?: unknown, excludedRevisionTargets?: unknown): Promise<Record<string, unknown>> {
  return bridge(config, {
    action: "apply_placement", request_id: requestId, raw_model_response: raw, statement,
    selected_entry: selectedEntry, memory_workspace: config.memory_workspace ?? config.statement_store_workspace,
    revision_confirmation: revisionConfirmation, excluded_revision_targets: excludedRevisionTargets,
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
