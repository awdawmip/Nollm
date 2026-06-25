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

function eventIdentity(event: unknown): { runId?: string; sessionId?: string } {
  const e = event as Record<string, unknown>;
  return {
    runId: typeof e.runId === "string" ? e.runId : undefined,
    sessionId: typeof e.sessionId === "string" ? e.sessionId : undefined,
  };
}

const CAPTURE_SCHEMA = "nollm.provider.capture.v2";

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
      const identity = resolveNollmTurnIdentity(ctxTyped, eventIdentity(event), {
        allowAgentIds: config.allowAgentIds,
      });
      if (identity.warnings.some((w) => w.startsWith("agent_id_rejected"))) {
        api.logger.warn(`Nollm agent rejected: ${identity.warnings.join("; ")}`);
        return { prependContext: makeUnavailableBoundary() };
      }
      // D3: fail-close on incomplete durable identity
      if (!identity.sessionId || !identity.runId) {
        api.logger.warn(`Nollm prepare rejected: incomplete identity`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const messages = Array.isArray(event.messages) ? event.messages : [];
      const typedMessages = messages as TurnMessage[];
      const query = extractLatestUserText(typedMessages);

      const result = await runSidecarCommand(config, "prepare", {
        schema: "nollm.provider.prepare.v1",
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

      // D3: Pre-validate sidecar envelope, then add identity warnings,
      // then do final budget check on the complete rendered text.
      const preValidated = validatePrepareResult(result, {
        maxFacts: config.maxFacts,
        maxContextCharacters: config.maxContextCharacters,
        maxCharacters: config.maxCharacters,
      });
      if (!preValidated.ok) {
        api.logger.warn(`Nollm prepare validation failed: ${preValidated.error.message}`);
        return { prependContext: makeUnavailableBoundary() };
      }

      const ctxEnvelope = (preValidated as unknown as { context: MemoryContextEnvelope }).context;
      // D3: Add identity warnings BEFORE final budget check
      if (identity.warnings.length > 0) {
        ctxEnvelope.warnings.push(...identity.warnings);
      }

      // D3: Final budget check on the complete rendered text including identity warnings
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
        const identity = resolveNollmTurnIdentity(ctxTyped, eventIdentity(event), {
          allowAgentIds: config.allowAgentIds,
        });
        if (identity.warnings.some((w) => w.startsWith("agent_id_rejected"))) {
          api.logger.warn(`Nollm capture skipped: agent rejected`);
          return;
        }
        // D3: fail-close on incomplete durable identity
        if (!identity.sessionId || !identity.runId) {
          api.logger.warn(`Nollm capture rejected: incomplete identity`);
          return;
        }

        const messages = Array.isArray(event.messages) ? event.messages : [];
        const success = typeof event.success === "boolean" ? event.success : true;

        // D4: Python is the sole canonical capture identity authority.
        // TS forwards raw payload and accepts the returned receipt_id.
        // No TS-side duplicate authority; Python handles dedupe via atomic receipt publish.
        const result = await runSidecarCommand(config, "capture", {
          schema: CAPTURE_SCHEMA,
          agent_id: identity.agentId,
          session_id: identity.sessionId,
          run_id: identity.runId,
          success,
          messages,
        });
        if (!result.ok) {
          api.logger.warn(`Nollm capture failed: ${result.error.message}`);
          return;
        }

        const receipt = (result as unknown as { receipt: { receipt_id: string; reused?: boolean } }).receipt;
        api.logger.info(`Nollm capture ${receipt.reused ? "idempotent: Python reused receipt " : "stored receipt "}${receipt.receipt_id}`);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        api.logger.warn(`Nollm capture exception: ${message}`);
      }
    }
  );
}
