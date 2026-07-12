import { spawn } from "node:child_process";
import { appendFile, mkdir } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { dirname, join } from "node:path";
import { buildJsonPluginConfigSchema, definePluginEntry, type OpenClawPluginApi } from "openclaw/plugin-sdk/core";

export type RunResult = { code: number; stdout: string; stderr: string };
export type DreamConfig = {
  enabled?: boolean; python_executable?: string; nollm_repo_root?: string;
  statement_store_workspace?: string; write_mode?: "shadow" | "statement-store";
  model_mode?: "inherit" | "dedicated"; model?: string; allowed_models?: string[];
  prompt_version?: string; timeout_ms?: number; max_material_chars?: number;
  max_statements?: number; max_statement_chars?: number; max_total_chars?: number;
  persist_subagent_transcripts?: boolean; debug_trace?: boolean; evidence_path?: string;
};

const JSON_SCHEMA = {
  type: "object", additionalProperties: false,
  properties: {
    enabled: { type: "boolean", default: true }, python_executable: { type: "string" }, nollm_repo_root: { type: "string" },
    statement_store_workspace: { type: "string" }, write_mode: { type: "string", enum: ["shadow", "statement-store"], default: "shadow" },
    model_mode: { type: "string", enum: ["inherit", "dedicated"], default: "inherit" }, model: { type: "string" },
    allowed_models: { type: "array", items: { type: "string" }, default: [] }, prompt_version: { type: "string", default: "dream-v1" },
    timeout_ms: { type: "integer", minimum: 1000, default: 120000 }, max_material_chars: { type: "integer", minimum: 1, default: 12000 },
    max_statements: { type: "integer", minimum: 1, default: 8 }, max_statement_chars: { type: "integer", minimum: 1, default: 4096 },
    max_total_chars: { type: "integer", minimum: 1, default: 8192 }, persist_subagent_transcripts: { type: "boolean", const: false, default: false },
    debug_trace: { type: "boolean", default: false }, evidence_path: { type: "string" },
  },
} as const;

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
  const wire = JSON.stringify(envelope, (_key, value: unknown) => typeof value === "string" ? wellFormedText(value) : value);
  const result = await run(config.python_executable!, ["-m", "nollm_openclaw_formation.bridge"], wire, config.timeout_ms, { ...process.env, PYTHONPATH: pythonPath(config) });
  if (result.code !== 0) return { ok: false, error: "bridge_process_error", detail: result.stderr };
  try { return JSON.parse(result.stdout); } catch { return { ok: false, error: "bridge_invalid_json", detail: result.stderr }; }
}

type Turn = { role: "user" | "assistant"; content_utf8: string };
type Pending = { users: Turn[]; inheritedModel?: string };

export function wellFormedText(value: string): string {
  return Array.from(value, character => {
    const unit = character.charCodeAt(0);
    return character.length === 1 && unit >= 0xd800 && unit <= 0xdfff ? "\ufffd" : character;
  }).join("");
}

function boundedTurns(users: Turn[], assistant: string, budget: number): Turn[] {
  const selected = [...users.slice(-2), { role: "assistant" as const, content_utf8: assistant }];
  let remaining = budget; const reversed: Turn[] = [];
  for (const turn of selected.reverse()) {
    if (remaining <= 0) break;
    const content = wellFormedText(turn.content_utf8.slice(0, remaining));
    if (content) reversed.push({ ...turn, content_utf8: content });
    remaining -= content.length;
  }
  return reversed.reverse();
}

function extractAssistantText(messages: unknown[]): string | undefined {
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

function extractUserTurns(messages: unknown[]): Turn[] {
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
  api.on("before_agent_run", (event, ctx) => {
    void trace(config, { status: "observed", hook: "before_agent_run", session_key: ctx.sessionKey, agent_id: ctx.agentId, message_provider: ctx.messageProvider, model_provider_id: ctx.modelProviderId, model_id: ctx.modelId });
    if (config.enabled === false || !ctx.sessionKey || ctx.agentId === "nollm-dream-agent" || !event.prompt.trim()) return;
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    current.users = [...current.users, { role: "user" as const, content_utf8: wellFormedText(event.prompt.trim()) }].slice(-2);
    if (ctx.modelProviderId && ctx.modelId) current.inheritedModel = `${ctx.modelProviderId}/${ctx.modelId}`;
    pending.set(ctx.sessionKey, current);
  });
  api.on("message_received", (event, ctx) => {
    if (config.enabled === false || !ctx.sessionKey || typeof event.content !== "string" || !event.content.trim()) return;
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    current.users = [...current.users, { role: "user" as const, content_utf8: wellFormedText(event.content.trim()) }].slice(-2);
    pending.set(ctx.sessionKey, current);
  });
  api.on("llm_output", (event, ctx) => {
    if (!ctx.sessionKey) return;
    const current: Pending = pending.get(ctx.sessionKey) ?? { users: [] };
    current.inheritedModel = event.resolvedRef ?? `${event.provider}/${event.model}`;
    pending.set(ctx.sessionKey, current);
  });
  const launch = async (sessionKey: string, assistant: string, marker: string, eligibleAt: number, sourceHook: "message_sent" | "agent_end", users?: Turn[], inheritedModel?: string) => {
    const deliveredAt = Date.now();
    if (config.enabled === false || !assistant.trim() || inFlight.has(sessionKey)) return;
    if (!config.python_executable || !config.nollm_repo_root) { await trace(config, { status: "defer", reason: "explicit_configuration_required", main_reply_delivered_at: deliveredAt }); return; }
    const current = pending.get(sessionKey) ?? { users: users ?? [], inheritedModel };
    if (!current.users.length && users?.length) current.users = users;
    if (!current.inheritedModel && inheritedModel) current.inheritedModel = inheritedModel;
    if (!current?.users.length) return;
    const model = config.model_mode === "dedicated" ? config.model : current.inheritedModel;
    if ((config.model_mode === "dedicated" && !model) || (config.allowed_models?.length && (!model || !config.allowed_models.includes(model)))) {
      await trace(config, { status: "defer", reason: "model_not_allowed", model }); return;
    }
    const idempotencyKey = createHash("sha256").update(`${sessionKey}\0${marker}`).digest("hex");
    if (scheduled.has(idempotencyKey)) return;
    scheduled.add(idempotencyKey);
    const requestId = `dream-request-${idempotencyKey}`;
    const request = {
      request_id: requestId,
      material: { material_id: `material-${idempotencyKey}`, turns: boundedTurns(current.users, assistant, config.max_material_chars ?? 12000) },
      max_statements: config.max_statements ?? 8, max_statement_chars: config.max_statement_chars ?? 4096,
      max_total_chars: config.max_total_chars ?? 8192, schema_version: "nollm_access_dream_formation_v1",
    };
    const built = await bridge(config, { action: "build_dream_prompt", request, prompt_version: config.prompt_version ?? "dream-v1" });
    if (built.ok !== true || typeof built.prompt !== "string") { await trace(config, { status: "error", stage: "build_prompt", ...built }); return; }
    inFlight.add(sessionKey);
    const dreamStartedAt = Date.now();
    try {
      const childSessionKey = `agent:nollm-dream-agent:subagent:${randomUUID()}`;
      const spawned = await api.runtime.subagent.run({
        sessionKey: childSessionKey, message: built.prompt,
        ...(config.model_mode === "dedicated" ? { model } : {}),
        lightContext: true, deliver: false, idempotencyKey,
      });
      await trace(config, { status: "started", request_id: requestId, session_key: sessionKey, child_session_key: childSessionKey, run_id: spawned.runId, model: model ?? "host-inherit", model_mode: config.model_mode ?? "inherit", prompt_version: built.prompt_version, prompt_sha256: built.prompt_sha256, schema_sha256: built.schema_sha256, source_hook: sourceHook, eligibility_at: eligibleAt, main_reply_delivered_at: deliveredAt, dream_started_at: dreamStartedAt, hook_scheduling_overhead_ms: dreamStartedAt - eligibleAt, deliver: false, visible_message_count: 0 });
      void completeDream(api, config, sessionKey, childSessionKey, spawned.runId, request, built, inFlight, dreamStartedAt);
    } catch (error) {
      inFlight.delete(sessionKey);
      await trace(config, { status: "error", stage: "spawn", request_id: requestId, error: String(error), main_reply_delivered_at: deliveredAt });
    }
  };
  api.on("message_sent", (event, ctx) => {
    if (!event.success || !ctx.sessionKey || !event.content.trim()) return;
    const content = wellFormedText(event.content);
    void launch(ctx.sessionKey, content, event.messageId ?? content, Date.now(), "message_sent");
  });
  api.on("agent_end", (event, ctx) => {
    void trace(config, { status: "observed", hook: "agent_end", session_key: ctx.sessionKey, agent_id: ctx.agentId, message_provider: ctx.messageProvider, success: event.success });
    if (!event.success || !ctx.sessionKey || (ctx.messageProvider && ctx.messageProvider !== "webchat") || ctx.agentId === "nollm-dream-agent") return;
    const assistant = extractAssistantText(event.messages);
    if (!assistant) return;
    const model = ctx.modelProviderId && ctx.modelId ? `${ctx.modelProviderId}/${ctx.modelId}` : undefined;
    const content = wellFormedText(assistant);
    void launch(ctx.sessionKey, content, event.runId ?? content, Date.now(), "agent_end", extractUserTurns(event.messages), model);
  });
}

async function completeDream(api: OpenClawPluginApi, config: DreamConfig, parentSession: string, childSession: string, runId: string, request: object, built: Record<string, unknown>, inFlight: Set<string>, startedAt: number): Promise<void> {
  try {
    const waited = await api.runtime.subagent.waitForRun({ runId, timeoutMs: config.timeout_ms ?? 120000 });
    if (waited.status !== "ok") { await trace(config, { status: waited.status, stage: "subagent", run_id: runId, error: waited.error, dream_latency_ms: Date.now() - startedAt, visible_message_count: 0 }); return; }
    const session = await api.runtime.subagent.getSessionMessages({ sessionKey: childSession, limit: 20 });
    const raw = extractAssistantText(session.messages);
    if (!raw) { await trace(config, { status: "error", stage: "empty_output", run_id: runId, visible_message_count: 0 }); return; }
    const parsed = await bridge(config, { action: "parse_dream_result", request, raw_model_response: raw, result_id: `dream-result-${runId}`, statement_store_workspace: config.write_mode === "statement-store" ? config.statement_store_workspace : null });
    await trace(config, { status: parsed.ok === true ? "completed" : "error", stage: "parse_store", run_id: runId, parent_session_key: parentSession, dream_latency_ms: Date.now() - startedAt, write_mode: config.write_mode ?? "shadow", visible_message_count: 0, python_semantic_fallback: false, prompt_version: built.prompt_version, ...parsed });
  } catch (error) {
    await trace(config, { status: "error", stage: "completion", run_id: runId, error: String(error), visible_message_count: 0 });
  } finally {
    inFlight.delete(parentSession);
    if (!config.persist_subagent_transcripts) { try { await api.runtime.subagent.deleteSession({ sessionKey: childSession, deleteTranscript: true }); } catch { /* diagnostic cleanup is best effort */ } }
  }
}

const plugin = definePluginEntry({
  id: "nollm-formation", name: "Nollm Invisible Dream Agent",
  description: "Post-delivery background MemoryStatement formation through an OpenClaw-owned subagent.",
  configSchema: buildJsonPluginConfigSchema(JSON_SCHEMA),
  register: registerDreamAgent,
});

export default plugin;
