import type {
  MemoryPluginCapability,
} from "openclaw/plugin-sdk/memory-core-host-runtime-core";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";
import { createHash } from "node:crypto";
import { configurationRequiredStatus, normalizeConfig } from "./config.js";
import { formatMemoryContext, makeUnavailableBoundary } from "./hook-context.js";
import { runSidecarCommand } from "./sidecar.js";
import { validatePrepareResult, validateCaptureResult } from "./context-validation.js";
import { extractLatestUserText, resolveNollmTurnIdentity } from "./identity.js";
import type { HookContext, TurnMessage } from "./identity.js";
import type { MemoryContextEnvelope, PluginConfig } from "./types.js";

function eventIdentity(event: unknown): { runId?: string; sessionId?: string } {
  const e = event as Record<string, unknown>;
  return {
    runId: typeof e.runId === "string" ? e.runId : undefined,
    sessionId: typeof e.sessionId === "string" ? e.sessionId : undefined,
  };
}

function turnReceiptId(identity: { agentId?: string; sessionId?: string; runId?: string }, eventKind: string): string {
  return createHash("sha256")
    .update(`${identity.agentId || ""}\0${identity.sessionId || ""}\0${identity.runId || ""}\0${eventKind}`)
    .digest("hex")
    .slice(0, 32);
}

const ACTIVE_STATUS_SCHEMA = "nollm.active_memory_status.v1";
const ACTIVE_PREPARE_SCHEMA = "nollm.active_memory_prepare.v1";
const ACTIVE_CAPTURE_SCHEMA = "nollm.active_memory_capture.v1";

function extractPrepareQuery(event: unknown): string {
  const e = event as Record<string, unknown>;
  if (Array.isArray(e.messages)) {
    const fromMessages = extractLatestUserText(e.messages as TurnMessage[]);
    if (fromMessages) return fromMessages;
  }
  if (typeof e.prompt === "string" && e.prompt.trim()) {
    return e.prompt;
  }
  return "";
}

export function createNollmProvider(api: OpenClawPluginApi): void {
  const rawConfig = (api.pluginConfig ?? {}) as PluginConfig;
  const configRequired = configurationRequiredStatus(rawConfig);
  let config: ReturnType<typeof normalizeConfig> | undefined;
  try {
    if (configRequired.ok) {
      config = normalizeConfig(rawConfig);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    api.logger.warn(`Nollm active memory provider config invalid: ${message}`);
  }

  const trialId = config?.trialId;

  const capability: MemoryPluginCapability = {
    promptBuilder: () => [],
    flushPlanResolver: () => null,
    runtime: undefined,
  };
  api.registerMemoryCapability(capability);

  api.on(
    "agent_turn_prepare",
    async (event, ctx: unknown) => {
      if (!config) {
        return { prependContext: makeUnavailableBoundary() };
      }

      const ctxTyped = (ctx ?? {}) as HookContext;
      const identity = resolveNollmTurnIdentity(ctxTyped, eventIdentity(event));
      if (identity.warnings.some((w) => w.startsWith("agent_id_rejected"))) {
        api.logger.warn(`Nollm agent rejected: ${identity.warnings.join("; ")}`);
        return { prependContext: makeUnavailableBoundary() };
      }
      if (!identity.agentId || !identity.sessionId || !identity.runId) {
        api.logger.warn(`Nollm prepare rejected: incomplete identity`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const query = extractPrepareQuery(event);
      if (!query) {
        const eventKeys = Object.keys(event as Record<string, unknown>).sort().join(",");
        api.logger.warn(`Nollm prepare skipped: no current user query; event_keys=${eventKeys}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const result = await runSidecarCommand(config, "active-prepare", {
        schema: ACTIVE_PREPARE_SCHEMA,
        agent_id: identity.agentId,
        session_id: identity.sessionId,
        run_id: identity.runId,
        query,
        budget: {
          max_facts: config.maxFacts,
          max_context_characters: config.maxContextCharacters,
        },
        trial_id: trialId,
        operation_id: config.operationId,
        turn_receipt_id: config.operationId ? turnReceiptId(identity, "prepare") : undefined,
        event_source: config.operationId ? "agent_hook" : "preflight",
      });

      if (!result.ok) {
        api.logger.warn(`Nollm active prepare failed: ${result.error.message}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const preValidated = validatePrepareResult(result, {
        maxFacts: config.maxFacts,
        maxContextCharacters: config.maxContextCharacters,
      });
      if (!preValidated.ok) {
        api.logger.warn(`Nollm prepare validation failed: ${preValidated.error.message}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const ctxEnvelope = preValidated.context as MemoryContextEnvelope;
      if (identity.warnings.length > 0) {
        ctxEnvelope.warnings.push(...identity.warnings);
      }

      const finalRendered = formatMemoryContext(ctxEnvelope);
      if (finalRendered.length > config.maxContextCharacters) {
        api.logger.warn("Nollm context exceeds final budget after identity warnings");
        return { prependContext: makeUnavailableBoundary() };
      }
      return { prependContext: finalRendered };
    }
  );

  api.on(
    "agent_end",
    async (event, ctx: unknown) => {
      if (!config) {
        return;
      }
      try {
        const ctxTyped = (ctx ?? {}) as HookContext;
        const identity = resolveNollmTurnIdentity(ctxTyped, eventIdentity(event));
        if (identity.warnings.some((w) => w.startsWith("agent_id_rejected"))) {
          api.logger.warn(`Nollm capture skipped: agent rejected`);
          return;
        }
        if (!identity.agentId || !identity.sessionId || !identity.runId) {
          api.logger.warn(`Nollm capture rejected: incomplete identity`);
          return;
        }

        if (typeof event.success !== "boolean") {
          api.logger.warn(`Nollm capture rejected: event.success is not a boolean`);
          return;
        }
        if (!Array.isArray(event.messages)) {
          api.logger.warn(`Nollm capture rejected: event.messages is not an array`);
          return;
        }
        const currentUserMessage = extractLatestUserText(event.messages as TurnMessage[]);
        if (!currentUserMessage) {
          api.logger.warn(`Nollm capture skipped: no current user message`);
          return;
        }
        const messages = [{ role: "user", content: currentUserMessage }];

        const result = await runSidecarCommand(config, "active-capture", {
          schema: ACTIVE_CAPTURE_SCHEMA,
          agent_id: identity.agentId,
          session_id: identity.sessionId,
          run_id: identity.runId,
          success: event.success,
          messages,
          trial_id: trialId,
          operation_id: config.operationId,
          turn_receipt_id: config.operationId ? turnReceiptId(identity, "capture") : undefined,
          event_source: config.operationId ? "agent_hook" : "preflight",
        });
        if (!result.ok) {
          api.logger.warn(`Nollm capture failed: ${result.error.message}`);
          return;
        }

        if (!validateCaptureResult(result)) {
          api.logger.warn(`Nollm capture returned invalid schema`);
          return;
        }

        const capture = (result as unknown as { capture: { promoted_count: number; deduplicated_count: number } }).capture;
        api.logger.info(
          `Nollm active capture: promoted=${capture.promoted_count}, deduplicated=${capture.deduplicated_count}`
        );
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        api.logger.warn(`Nollm capture exception: ${message}`);
      }
    }
  );
}
