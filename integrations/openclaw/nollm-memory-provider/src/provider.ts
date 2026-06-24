import type {
  MemoryPluginCapability,
} from "openclaw/plugin-sdk/memory-core-host-runtime-core";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";
import { configurationRequiredStatus, normalizeConfig } from "./config.js";
import { formatMemoryContext, makeUnavailableBoundary } from "./hook-context.js";
import { createNollmCompatibilityRuntime } from "./memory-runtime.js";
import { runSidecarCommand } from "./sidecar.js";
import { validatePrepareResult } from "./context-validation.js";
import { extractLatestUserText, resolveNollmTurnIdentity } from "./identity.js";
import type { HookContext, TurnMessage } from "./identity.js";
import type { MemoryContextEnvelope, PluginConfig } from "./types.js";

const CAPTURE_PROTOCOL_VERSION = "nollm.capture.v1";

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
    api.logger.warn(`Nollm memory provider config invalid: ${message}`);
  }

  // Track capture receipts for idempotency within this process
  const captureRegistry = new Map<string, { receiptId: string; eventHash: string }>();

  const capability: MemoryPluginCapability = {
    promptBuilder: () => [],
    flushPlanResolver: () => null,
    runtime: config ? createNollmCompatibilityRuntime(config) : undefined,
  };
  api.registerMemoryCapability(capability);

  api.on(
    "agent_turn_prepare",
    async (event, ctx: unknown) => {
      if (!config) {
        return { prependContext: makeUnavailableBoundary() };
      }

      const ctxTyped = (ctx ?? {}) as HookContext;
      const identity = resolveNollmTurnIdentity(ctxTyped, {
        allowAgentIds: config.allowAgentIds,
      });
      if (identity.warnings.some((w) => w.startsWith("agent_id_rejected"))) {
        api.logger.warn(`Nollm agent rejected: ${identity.warnings.join("; ")}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const messages = Array.isArray(event.messages) ? event.messages : [];
      const typedMessages = messages as TurnMessage[];
      const query = extractLatestUserText(typedMessages);

      const result = await runSidecarCommand(config, "prepare", {
        schema: "nollm.provider.prepare.v1",
        request_id: `prepare-${identity.runId}`,
        agent_id: identity.agentId,
        session_id: identity.sessionId,
        run_id: identity.runId,
        messages: [{ role: "user", content: query }],
        budget: {
          max_facts: config.maxFacts,
          max_characters: config.maxCharacters,
        },
      });

      if (!result.ok) {
        api.logger.warn(`Nollm prepare failed: ${result.error.message}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const validated = validatePrepareResult(result, { maxFacts: config.maxFacts,
        maxContextCharacters: config.maxContextCharacters,

        maxCharacters: config.maxCharacters,
      });
      if (!validated.ok) {
        api.logger.warn(`Nollm prepare validation failed: ${validated.error.message}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const ctxEnvelope = (validated as unknown as { context: MemoryContextEnvelope }).context;
      if (identity.warnings.length > 0) {
        ctxEnvelope.warnings.push(...identity.warnings);
      }
      return { prependContext: formatMemoryContext(ctxEnvelope) };
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
        const identity = resolveNollmTurnIdentity(ctxTyped, {
          allowAgentIds: config.allowAgentIds,
        });
        if (identity.warnings.some((w) => w.startsWith("agent_id_rejected"))) {
          api.logger.warn(`Nollm capture skipped: agent rejected`);
          return;
        }

        const messages = Array.isArray(event.messages) ? event.messages : [];
        const success = typeof event.success === "boolean" ? event.success : true;

        // Compute stable canonical event hash for idempotency
        const canonicalEvent = JSON.stringify({
          agent_id: identity.agentId,
          session_id: identity.sessionId,
          run_id: identity.runId,
          success,
          messages,
        });
        const crypto = await import("node:crypto");
        const eventHash = crypto.createHash("sha256").update(canonicalEvent).digest("hex");
        const captureKey = `${identity.agentId}:${identity.sessionId}:${identity.runId}`;

        // Check for existing receipt (idempotent)
        const existing = captureRegistry.get(captureKey);
        if (existing && existing.eventHash === eventHash) {
          // Same event already captured - return existing receipt
          api.logger.info(`Nollm capture idempotent: reusing receipt ${existing.receiptId}`);
          return;
        }
        if (existing && existing.eventHash !== eventHash) {
          // Collision: same key but different content
          api.logger.warn(`Nollm capture collision: same key but different event hash`);
          return;
        }

        const result = await runSidecarCommand(config, "capture", {
          schema: "nollm.provider.capture.v1",
          request_id: `capture-${identity.runId}`,
          agent_id: identity.agentId,
          session_id: identity.sessionId,
          run_id: identity.runId,
          success,
          messages,
          event_hash: eventHash,
          capture_protocol_version: CAPTURE_PROTOCOL_VERSION,
        });
        if (!result.ok) {
          api.logger.warn(`Nollm capture failed: ${result.error.message}`);
          return;
        }

        const receipt = (result as unknown as { receipt: { receipt_id: string } }).receipt;
        captureRegistry.set(captureKey, { receiptId: receipt.receipt_id, eventHash });
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        api.logger.warn(`Nollm capture exception: ${message}`);
      }
    }
  );
}
