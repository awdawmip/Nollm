import { randomUUID } from "node:crypto";

export const MEMORY_SEARCH_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    query: { type: "string" },
    maxResults: { type: "integer", minimum: 1, maximum: 32 },
    minScore: { type: "number" },
    corpus: { type: "string", enum: ["memory", "all"] },
    action: { type: "string", enum: ["surface", "open_region", "enter_locality", "select_fact", "none", "defer"] },
    operationId: { type: "string", minLength: 1, maxLength: 128 },
    regionId: { type: "string", minLength: 1, maxLength: 256 },
    entryId: { type: "string", minLength: 1, maxLength: 256 },
    candidateId: { type: "string", minLength: 1, maxLength: 256 },
    semanticRelation: { type: "string", enum: ["same", "revision", "related_distinct", "unrelated", "uncertain"] },
    recalledFactIds: { type: "array", maxItems: 16, items: { type: "string", minLength: 1, maxLength: 256 } }
  }
};

export const MEMORY_GET_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["path"],
  properties: {
    path: { type: "string", minLength: 1, maxLength: 1024 },
    from: { type: "integer", minimum: 1 },
    lines: { type: "integer", minimum: 1, maximum: 10000 },
    corpus: { type: "string", enum: ["memory", "all"] }
  }
};

const FIELD_SCOPE = {
  profile_id: "default_dream_v1",
  chart_id: "default",
  physical_layers: [0],
  reference_layer: 0,
  phase_policy: "physical_layer_mod8",
  max_relative_layer_delta: 8
};

const SURFACE_POLICY = {
  max_regions_per_page: 32,
  max_prompt_bytes: 65536,
  max_depth: 8,
  max_order: 8,
  support_limit: 4
};

function toolResult(details) {
  return { content: [{ type: "text", text: JSON.stringify(details) }], details };
}

function scopeKey(scope) {
  return `${scope.agentId}\0${scope.sessionKey ?? ""}\0${scope.workspace}`;
}

function cleanString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function isStatementItem(item) {
  return item !== null
    && typeof item === "object"
    && typeof item.statement_id === "string"
    && item.statement_id.length > 0
    && typeof item.content_utf8 === "string"
    && item.content_utf8.length > 0;
}

function standardResults(items, minScore) {
  const list = Array.isArray(items) ? items : [];
  const results = [];
  const count = Math.max(1, list.length);
  for (let index = 0; index < list.length; index += 1) {
    const item = list[index];
    if (!isStatementItem(item)) continue;
    const id = item.statement_id;
    const content = item.content_utf8;
    const score = Math.max(0.1, 1 - index / count);
    if (typeof minScore === "number" && score < minScore) continue;
    results.push({
      path: `nollm://statement/${encodeURIComponent(id)}`,
      startLine: 1,
      endLine: Math.max(1, content.split(/\r?\n/).length),
      score,
      snippet: content,
      source: "memory",
      citation: `nollm:${id}`,
      statement_id: id,
      geometry_ordered: true,
      score_is_not_truth_proof: true
    });
  }
  return results;
}

export class MemoryOperationRegistry {
  constructor({ ttlMs = 300000, capacity = 64 } = {}) {
    this.ttlMs = ttlMs;
    this.capacity = capacity;
    this.operations = new Map();
  }

  expire(now = Date.now()) {
    for (const [id, op] of this.operations) {
      if (op.expiresAt <= now) this.operations.delete(id);
    }
  }

  create(scope, request) {
    this.expire();
    if (this.operations.size >= this.capacity) {
      const oldest = [...this.operations.entries()].sort((a, b) => a[1].createdAt - b[1].createdAt)[0];
      if (oldest) this.operations.delete(oldest[0]);
    }
    const operationId = `memory-search-${randomUUID()}`;
    const now = Date.now();
    const op = { operationId, scopeKey: scopeKey(scope), request, history: [], createdAt: now, expiresAt: now + this.ttlMs };
    this.operations.set(operationId, op);
    return op;
  }

  get(operationId, scope) {
    this.expire();
    const op = this.operations.get(operationId);
    if (!op) return undefined;
    if (op.scopeKey !== scopeKey(scope)) return undefined;
    op.expiresAt = Date.now() + this.ttlMs;
    return op;
  }

  delete(operationId) {
    this.operations.delete(operationId);
  }
}

function continuation(status, operationId, payload) {
  return {
    status,
    operationId,
    results: [],
    ...payload,
    nollm: {
      operation_neutral: true,
      single_entry_only: true,
      continue_with_same_tool: true,
      path_is_not_truth_proof: true
    }
  };
}

export function createMemorySearchFactory({ bridge, registry, config }) {
  return (ctx) => {
    const agentId = cleanString(ctx?.agentId);
    if (!agentId) return null;
    const scope = {
      agentId,
      sessionKey: cleanString(ctx?.sessionKey) ?? "",
      workspace: bridge.workspaceForAgent(agentId)
    };
    return {
      name: "memory_search",
      label: "Memory Search",
      description: "Search Nollm geometry memory. The first call returns a Surface; continue with this same tool until one fact is selected or none is returned.",
      parameters: MEMORY_SEARCH_SCHEMA,
      async execute(_toolCallId, rawParams = {}, signal) {
        const params = rawParams && typeof rawParams === "object" ? rawParams : {};
        const action = cleanString(params.action) ?? "surface";
        if (action === "surface") {
          const query = cleanString(params.query);
          if (!query || params.operationId) return toolResult({ status: "invalid_parameters", results: [] });
          if (!bridge.available) return toolResult({ status: "unavailable", reason: "Nollm runtime is not installed", results: [] });
          const request = {
            scope_id: `agent:${agentId}`,
            workspace_id: scope.workspace,
            stimulus_material: [query],
            optional_pending_proposition: null,
            field_scope: FIELD_SCOPE,
            surface_policy: SURFACE_POLICY,
            locality_max_results: config.maxResults,
            locality_max_chars: config.maxContextCharacters,
            vacancy_budget: 1,
            expected_state_identity: null,
            created_at_ms: null,
            ttl_ms: config.operationTtlMs
          };
          const op = registry.create(scope, request);
          const response = await bridge.call({
            action: "run_field_encounter",
            memory_workspace: scope.workspace,
            operation_id: op.operationId,
            request,
            history: []
          }, signal);
          if (response?.ok !== true || response?.status !== "surface") {
            registry.delete(op.operationId);
            return toolResult({ status: "unavailable", reason: response?.error ?? response?.status ?? "field_unavailable", results: [] });
          }
          return toolResult(continuation("surface", op.operationId, { page: response.page, rootIdentity: response.root_identity }));
        }

        const operationId = cleanString(params.operationId);
        if (!operationId) return toolResult({ status: "invalid_parameters", results: [] });
        const op = registry.get(operationId, scope);
        if (!op) return toolResult({ status: "operation_unavailable", results: [] });

        if (action === "open_region") {
          const regionId = cleanString(params.regionId);
          if (!regionId) return toolResult({ status: "invalid_parameters", operationId, results: [] });
          op.history.push({ action: "open_region", region_id: regionId });
          const response = await bridge.call({ action: "run_field_encounter", memory_workspace: scope.workspace, operation_id: operationId, request: op.request, history: op.history }, signal);
          if (response?.ok !== true || response?.status !== "region") op.history.pop();
          return toolResult(continuation(response?.status ?? "unavailable", operationId, { page: response?.page, reason: response?.error }));
        }

        if (action === "enter_locality") {
          const regionId = cleanString(params.regionId);
          const entryId = cleanString(params.entryId);
          if (!regionId || !entryId) return toolResult({ status: "invalid_parameters", operationId, results: [] });
          op.history.push({ action: "enter_locality", region_id: regionId, entry_id: entryId });
          const response = await bridge.call({ action: "run_field_encounter", memory_workspace: scope.workspace, operation_id: operationId, request: op.request, history: op.history }, signal);
          if (response?.ok !== true || response?.status !== "locality") op.history.pop();
          return toolResult(continuation(response?.status ?? "unavailable", operationId, { locality: response, reason: response?.error }));
        }

        if (action === "none" || action === "defer") {
          const response = await bridge.call({
            action: "run_field_encounter",
            memory_workspace: scope.workspace,
            operation_id: operationId,
            request: op.request,
            history: op.history,
            terminal: { action, candidate_id: null, semantic_relation: null, recalled_fact_ids: [] }
          }, signal);
          registry.delete(operationId);
          return toolResult({ status: response?.status === "terminal" ? "complete_none" : "unavailable", operationId, results: [], terminal: response });
        }

        if (action === "select_fact") {
          const candidateId = cleanString(params.candidateId);
          if (!candidateId) return toolResult({ status: "invalid_parameters", operationId, results: [] });
          const recalledFactIds = Array.isArray(params.recalledFactIds) && params.recalledFactIds.every((item) => typeof item === "string")
            ? params.recalledFactIds
            : [candidateId];
          const response = await bridge.call({
            action: "run_field_encounter",
            memory_workspace: scope.workspace,
            operation_id: operationId,
            request: op.request,
            history: op.history,
            terminal: {
              action: "select_fact",
              candidate_id: candidateId,
              semantic_relation: cleanString(params.semanticRelation) ?? "same",
              recalled_fact_ids: recalledFactIds
            }
          }, signal);
          registry.delete(operationId);
          if (response?.ok !== true || response?.status !== "terminal") {
            return toolResult({ status: "unavailable", operationId, results: [], reason: response?.error ?? response?.status });
          }
          const statementIds = Array.isArray(response.recalled_statement_ids) ? response.recalled_statement_ids : [];
          const projection = await bridge.call({
            action: "read_field_encounter_statements",
            statement_ids: statementIds,
            memory_workspace: scope.workspace,
            max_statements: params.maxResults ?? config.maxResults,
            max_chars: config.maxContextCharacters
          }, signal);
          const results = projection?.ok === true
            ? standardResults(projection.items, params.minScore)
            : [];
          return toolResult({
            status: results.length ? "complete" : "complete_none",
            operationId,
            results,
            terminal: response,
            staleStatementIds: projection?.stale_statement_ids ?? [],
            geometryOrdered: true,
            hiddenReaderCalls: 0
          });
        }

        return toolResult({ status: "invalid_action", operationId, results: [] });
      }
    };
  };
}

function statementIdFromPath(value) {
  const prefix = "nollm://statement/";
  if (typeof value !== "string" || !value.startsWith(prefix)) return undefined;
  try { return decodeURIComponent(value.slice(prefix.length)); } catch { return undefined; }
}

export function createMemoryGetFactory({ bridge, config }) {
  return (ctx) => {
    const agentId = cleanString(ctx?.agentId);
    if (!agentId) return null;
    const workspace = bridge.workspaceForAgent(agentId);
    return {
      name: "memory_get",
      label: "Memory Get",
      description: "Read one exact current Nollm MemoryStatement returned by memory_search.",
      parameters: MEMORY_GET_SCHEMA,
      async execute(_toolCallId, rawParams = {}, signal) {
        const params = rawParams && typeof rawParams === "object" ? rawParams : {};
        const statementId = statementIdFromPath(params.path);
        if (!statementId) return toolResult({ status: "not_found", path: params.path, text: "" });
        if (!bridge.available) return toolResult({ status: "unavailable", path: params.path, text: "" });
        const projection = await bridge.call({
          action: "read_field_encounter_statements",
          statement_ids: [statementId],
          memory_workspace: workspace,
          max_statements: 1,
          max_chars: config.maxContextCharacters
        }, signal);
        const item = projection?.ok === true && Array.isArray(projection.items) ? projection.items[0] : undefined;
        if (!isStatementItem(item)) {
          return toolResult({ status: "not_found", path: params.path, text: "" });
        }
        const sourceLines = item.content_utf8.split(/\r?\n/);
        const from = Number.isInteger(params.from) ? Math.max(1, params.from) : 1;
        const lineCount = Number.isInteger(params.lines) ? Math.max(1, params.lines) : sourceLines.length;
        const slice = sourceLines.slice(from - 1, from - 1 + lineCount);
        const nextFrom = from - 1 + lineCount < sourceLines.length ? from + lineCount : undefined;
        return toolResult({
          status: "complete",
          path: params.path,
          text: slice.join("\n"),
          from,
          lines: slice.length,
          truncated: nextFrom !== undefined,
          ...(nextFrom ? { nextFrom } : {}),
          statementId: item.statement_id,
          currentStatementProjection: true
        });
      }
    };
  };
}
