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

function standardResults(items, minScore) {
  const list = Array.isArray(items) ? items : [];
  const results = [];
  const count = Math.max(1, list.length);
  for (let index = 0; index < list.length; index += 1) {
    const item = list[index];
    if (!item || typeof item !== "object") continue;
    const id = cleanString(item.statement_id);
    const content = typeof item.content_utf8 === "string" ? item.content_utf8 : "";
    if (!id || !content) continue;
    const score = Math.max(0.1, 1 - index / count);
    if (typeof minScore === "number" && score < minScore) continue;
    results.push({
      path: `nolm://statement/${encodeURIComponent(id)}`,
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
    this.ttlMs = ttlMs°¢F†—2æ66—G’Ò66—G“°¢F†—2æ÷W&F–öç2ÒæWrÖ‚“°¢Ð ¢W‡—&R†æ÷rÒFFRææ÷r‚’’°¢f÷"†6öç7B¶–BÂ÷ÒöbF†—2æ÷W&F–öç2’°¢–b†÷æW‡—&W4BÃÒæ÷r’F†—2æ÷W&F–öç2æFVÆWFR†–B“°¢Ð¢Ð ¢7&VFR‡66÷RÂ&WVW7B’°¢F†—2æW‡—&R‚“°¢–b‡F†—2æ÷W&F–öç2ç6—¦RãÒF†—2æ66—G’’°¢6öç7BöÆFW7BÒ²ââçF†—2æ÷W&F–öç2æVçG&–W2‚•Òç6÷'B‚†Â"’Óâ³Òæ7&VFVDBÒ%³Òæ7&VFVDB•³Ó°¢–b†öÆFW7B’F†—2æ÷W&F–öç2æFVÆWFR†öÆFW7E³Ò“°¢Ð¢6öç7B÷W&F–öä–BÒÖVÖ÷'’×6V&6‚ÒG·&æFöÕUT”B‚—Ö°¢6öç7Bæ÷rÒFFRææ÷r‚“°¢6öç7B÷Ò²÷W&F–öä–BÂ66÷T¶W“¢66÷T¶W’‡66÷R’Â&WVW7BÂ†—7F÷'“¢µÒÂ7&VFVDC¢æ÷rÂW‡—&W4C¢æ÷r²F†—2çGFÄ×2Ó°¢F†—2æ÷W&F–öç2ç6WB†÷W&F–öä–BÂ÷“°¢&WGW&â÷°¢Ð ¢vWB†÷W&F–öä–BÂ66÷R’°¢F†—2æW‡—&R‚“°¢6öç7B÷ÒF†—2æ÷W&F–öç2ævWB†÷W&F–öä–B“°¢–b‚÷’&WGW&âVæFVf–æVC°¢–b†÷ç66÷T¶W’ÓÒ66÷T¶W’‡66÷R’’&WGW&âVæFVf–æVC°¢÷æW‡—&W4BÒFFRææ÷r‚’²F†—2çGFÄ×;
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
            history: op.historx°(€€€€€€€€€€€Ñ•Éµ¥¹…°èì(€€€€€€€€€€€€€…Ñ¥½¸è€‰Í•±•Ñ}™…Ðˆ°(€€€€€€€€€€€€€…¹‘¥‘…Ñ•}¥è…¹‘¥‘…Ñ•%°(€€€€€€€€€€€€€Í•µ…¹Ñ¥}É•±…Ñ¥½¸è±•…¹MÑÉ¥¹œ¡Á…É…µÌ¹Í•µ…¹Ñ¥I•±…Ñ¥½¸¤€üü€‰Í…µ”ˆ°(€€€€€€€€€€€€€É•…±±•‘}™…Ñ}¥‘ÌèÉ•…±±•‘…Ñ%‘Ì(€€€€€€€€€€€ô(€€€€€€€€€ô°Í¥¹…°¤ì(€€€€€€€€€É•¥ÍÑÉä¹‘•±•Ñ”¡½Á•É…Ñ¥½¹%¤ì(€€€€€€€€€¥˜€¡É•ÍÁ½¹Í”ü¹½¬€„ôôÑÉÕ”ñðÉ•ÍÁ½¹Í”ü¹ÍÑ…ÑÕÌ€„ôô€‰Ñ•Éµ¥¹…°ˆ¤ì(€€€€€€€€€€€É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ìÍÑ…ÑÕÌè€‰Õ¹…Ù…¥±…‰±”ˆ°½Á•É…Ñ¥½¹%°É•ÍÕ±ÑÌèmt°É•…Í½¸èÉ•ÍÁ½¹Í”ü¹•ÉÉ½È€üüÉ•ÍÁ½¹Í”ü¹ÍÑ…ÑÕÌô¤ì(€€€€€€€€€ô(€€€€€€€€€½¹ÍÐÍÑ…Ñ•µ•¹Ñ%‘Ì€ôÉÉ…ä¹¥ÍÉÉ…ä¡É•ÍÁ½¹Í”¹É•…±±•‘}ÍÑ…Ñ•µ•¹Ñ}¥‘Ì¤€üÉ•ÍÁ½¹Í”¹É•…±±•‘}ÍÑ…Ñ•µ•¹Ñ}¥‘Ì€èmtì(€€€€€€€€€½¹ÍÐÁÉ½©•Ñ¥½¸€ô…Ý…¥Ð‰É¥‘”¹…±°¡ì(€€€€€€€€€€€…Ñ¥½¸è€‰É•…‘}™¥•±‘}•¹½Õ¹Ñ•É}ÍÑ…Ñ•µ•¹ÑÌˆ°(€€€€€€€€€€€ÍÑ…Ñ•µ•¹Ñ}¥‘ÌèÍÑ…Ñ•µ•¹Ñ%‘Ì°(€€€€€€€€€€€µ•µ½Éå}Ý½É­ÍÁ…”èÍ½Á”¹Ý½É­ÍÁ…”°(€€€€€€€€€€€µ…á}ÍÑ…Ñ•µ•¹ÑÌèÁ…É…µÌ¹µ…áI•ÍÕ±ÑÌ€üü½¹™¥œ¹µ…áI•ÍÕ±ÑÌ°(€€€€€€€€€€€µ…á}¡…ÉÌè½¹™¥œ¹µ…á½¹Ñ•áÑ¡…É…Ñ•ÉÌ(€€€€€€€€€ô°Í¥¹…°¤ì(€€€€€€€€€½¹ÍÐÉ•ÍÕ±ÑÌ€ôÁÉ½©•Ñ¥½¸ü¹½¬€ôôôÑÉÕ”(€€€€€€€€€€€€üÍÑ…¹‘…É‘I•ÍÕ±ÑÌ¡ÁÉ½©•Ñ¥½¸¹¥Ñ•µÌ°Á…É…µÌ¹µ¥¹M½É”¤(€€€€€€€€€€€€èmtì(€€€€€€€€€É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ì(€€€€€€€€€€€ÍÑ…ÑÕÌèÉ•ÍÕ±ÑÌ¹±•¹Ñ €ü€‰½µÁ±•Ñ”ˆ€è€‰½µÁ±•Ñ•}¹½¹”ˆ°(€€€€€€€€€€€½Á•É…Ñ¥½¹%°(€€€€€€€€€€€É•ÍÕ±ÑÌ°(€€€€€€€€€€€Ñ•Éµ¥¹…°èÉ•ÍÁ½¹Í”°(€€€€€€€€€€€ÍÑ…±•MÑ…Ñ•µ•¹Ñ%‘ÌèÁÉ½©•Ñ¥½¸ü¹ÍÑ…±•}ÍÑ…Ñ•µ•¹Ñ}¥‘Ì€üümt°(€€€€€€€€€€€•½µ•ÑÉå=É‘•É•èÑÉÕ”°(€€€€€€€€€€€¡¥‘‘•¹I•…‘•É…±±Ìè€À(€€€€€€€€€ô¤ì(€€€€€€€ô((€€€€€€€É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ìÍÑ…ÑÕÌè€‰¥¹Ù…±¥‘}…Ñ¥½¸ˆ°½Á•É…Ñ¥½¹%°É•ÍÕ±ÑÌèmtô¤ì(€€€€€ô(€€€ôì(€ôì)ô()™Õ¹Ñ¥½¸ÍÑ…Ñ•µ•¹Ñ%‘É½µA…Ñ ¡Ù…±Õ”¤ì(€½¹ÍÐÁÉ•™¥à€ô€‰¹½±±´è¼½ÍÑ…Ñ•µ•¹Ð¼ˆì(€¥˜€¡ÑåÁ•½˜Ù…±Õ”€„ôô€‰ÍÑÉ¥¹œˆñð€…Ù…±Õ”¹ÍÑ…ÉÑÍ]¥Ñ ¡ÁÉ•™¥à¤¤É•ÑÕÉ¸Õ¹‘•™¥¹•ì(€ÑÉäìÉ•ÑÕÉ¸‘•½‘•UI%½µÁ½¹•¹Ð¡Ù…±Õ”¹Í±¥”¡ÁÉ•™¥à¹±•¹Ñ ¤¤ìô…Ñ ìÉ•ÑÕÉ¸Õ¹‘•™¥¹•ìô)ô()•áÁ½ÉÐ™Õ¹Ñ¥½¸É•…Ñ•5•µ½Éå•Ñ…Ñ½Éä¡ì‰É¥‘”°½¹™¥œô¤ì(€É•ÑÕÉ¸€¡Ñà¤€ôøì(€€€½¹ÍÐ…•¹Ñ%€ô±•…¹MÑÉ¥¹œ¡Ñàü¹…•¹Ñ%¤ì(€€€¥˜€ ……•¹Ñ%¤É•ÑÕÉ¸¹Õ±°ì(€€€½¹ÍÐÝ½É­ÍÁ…”€ô‰É¥‘”¹Ý½É­ÍÁ…•½É•¹Ð¡…•¹Ñ%¤ì(€€€É•ÑÕÉ¸ì(€€€€€¹…µ”è€‰µ•µ½Éå}•Ðˆ°(€€€€€±…‰•°è€‰5•µ½Éä•Ðˆ°(€€€€€‘•ÍÉ¥ÁÑ¥½¸è€‰I•…½¹”•á…ÐÕÉÉ•¹Ð9½±±´5•µ½ÉåMÑ…Ñ•µ•¹ÐÉ•ÑÕÉ¹•‰äµ•µ½Éå}Í•…É ¸ˆ°(€€€€€Á…É…µ•Ñ•ÉÌè55=Ie}Q}M!5°(€€€€€…Íå¹Œ•á•ÕÑ”¡}Ñ½½±…±±%°É…ÝA…É…µÌ€ôíô°Í¥¹…°¤ì(€€€€€€€½¹ÍÐÁ…É…µÌ€ôÉ…ÝA…É…µÌ€˜˜ÑåÁ•½˜É…ÝA…É…µÌ€ôôô€‰½‰©•Ðˆ€üÉ…ÝA…É…µÌ€èíôì(€€€€€€€½¹ÍÐÍÑ…Ñ•µ•¹Ñ%€ôÍÑ…Ñ•µ•¹Ñ%‘É½µA…Ñ ¡Á…É…µÌ¹Á…Ñ ¤ì(€€€€€€€¥˜€ …ÍÑ…Ñ•µ•¹Ñ%¤É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ìÍÑ…ÑÕÌè€‰¹½Ñ}™½Õ¹ˆ°Á…Ñ èÁ…É…µÌ¹Á…Ñ °Ñ•áÐè€ˆˆô¤ì(€€€€€€€¥˜€ …‰É¥‘”¹…Ù…¥±…‰±”¤É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ìÍÑ…ÑÕÌè€‰Õ¹…Ù…¥±…‰±”ˆ°Á…Ñ èÁ…É…µÌ¹Á…Ñ °Ñ•áÐè€ˆˆô¤ì(€€€€€€€½¹ÍÐÁÉ½©•Ñ¥½¸€ô…Ý…¥Ð‰É¥‘”¹…±°¡ì(€€€€€€€€€…Ñ¥½¸è€‰É•…‘}™¥•±‘}•¹½Õ¹Ñ•É}ÍÑ…Ñ•µ•¹ÑÌˆ°(€€€€€€€€€ÍÑ…Ñ•µ•¹Ñ}¥‘ÌèmÍÑ…Ñ•µ•¹Ñ%‘t°(€€€€€€€€€µ•µ½Éå}Ý½É­ÍÁ…”èÝ½É­ÍÁ…”°(€€€€€€€€€µ…á}ÍÑ…Ñ•µ•¹ÑÌè€Ä°(€€€€€€€€€µ…á}¡…ÉÌè½¹™¥œ¹µ…á½¹Ñ•áÑ¡…É…Ñ•ÉÌ(€€€€€€€ô°Í¥¹…°¤ì(€€€€€€€½¹ÍÐ¥Ñ•´€ôÁÉ½©•Ñ¥½¸ü¹½¬€ôôôÑÉÕ”€˜˜ÉÉ…ä¹¥ÍÉÉ…ä¡ÁÉ½©•Ñ¥½¸¹¥Ñ•µÌ¤€üÁÉ½©•Ñ¥½¸¹¥Ñ•µÍlÁt€èÕ¹‘•™¥¹•ì(€€€€€€€¥˜€ …¥Ñ•´ñðÑåÁ•½˜¥Ñ•´¹½¹Ñ•¹Ñ}ÕÑ˜à€„ôô€‰ÍÑÉ¥¹œˆ¤ì(€€€€€€€€€É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ìÍÑ…ÑÕÌè€‰¹½Ñ}™½Õ¹ˆ°Á…Ñ èÁ…É…µÌ¹Á…Ñ °Ñ•áÐè€ˆˆô¤ì(€€€€€€€ô(€€€€€€€½¹ÍÐÍ½ÕÉ•1¥¹•Ì€ô¥Ñ•´¹½¹Ñ•¹Ñ}ÕÑ˜à¹ÍÁ±¥Ð ½qÈýq¸¼¤ì(€€€€€€€½¹ÍÐ™É½´€ô9Õµ‰•È¹¥Í%¹Ñ••È¡Á…É…µÌ¹™É½´¤€ü5…Ñ ¹µ…à Ä°Á…É…µÌ¹™É½´¤€è€Äì(€€€€€€€½¹ÍÐ±¥¹•½Õ¹Ð€ô9Õµ‰•È¹¥Í%¹Ñ••È¡Á…É…µÌ¹±¥¹•Ì¤€ü5…Ñ ¹µ…à Ä°Á…É…µÌ¹±¥¹•Ì¤€èÍ½ÕÉ•1¥¹•Ì¹±•¹Ñ ì(€€€€€€€½¹ÍÐÍ±¥”€ôÍ½ÕÉ•1¥¹•Ì¹Í±¥”¡™É½´€´€Ä°™É½´€´€Ä€¬±¥¹•½Õ¹Ð¤ì(€€€€€€€½¹ÍÐ¹•áÑÉ½´€ô™É½´€´€Ä€¬±¥¹•½Õ¹Ð€ðÍ½ÕÉ•1¥¹•Ì¹±•¹Ñ €ü™É½´€¬±¥¹•½Õ¹Ð€èÕ¹‘•™¥¹•ì(€€€€€€€É•ÑÕÉ¸Ñ½½±I•ÍÕ±Ð¡ì(€€€€€€€€€ÍÑ…ÑÕÌè€‰½µÁ±•Ñ”ˆ°(€€€€€€€€€Á…Ñ èÁ…É…µÌ¹Á…Ñ °(€€€€€€€€€Ñ•áÐèÍ±¥”¹©½¥¸ ‰q¸ˆ¤°(€€€€€€€€€™É½´°(€€€€€€€€€±¥¹•ÌèÍ±¥”¹±•¹Ñ °(€€€€€€€€€ÑÉÕ¹…Ñ•è¹•áÑÉ½´€„ôôÕ¹‘•™¥¹•°(€€€€€€€€€€¸¸¸¡¹•áÑÉ½´€üì¹•áÑÉ½´ô€èíô¤°(€€€€€€€€€ÍÑ…Ñ•µ•¹Ñ%è¥Ñ•´¹ÍÑ…Ñ•µ•¹Ñ}¥°(€€€€€€€€€ÕÉÉ•¹ÑMÑ…Ñ•µ•¹ÑAÉ½©•Ñ¥½¸èÑÉÕ”(€€€€€€€ô¤ì(€€€€€ô(€€€ôì(€ôì)ô(