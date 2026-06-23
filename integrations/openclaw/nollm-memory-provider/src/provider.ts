import type {
  MemoryPluginCapability,
} from "openclaw/plugin-sdk/memory-core-host-runtime-core";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";
import { configurationRequiredStatus, normalizeConfig } from "./config.js";
import { formatMemoryContext, makeUnavailableBoundary } from "./hook-context.js";
import { createNollmCompatibilityRuntime } from "./memory-runtime.js";
import { runSidecarCommand } from "./sidecar.js";
import type { MemoryContextEnvelope, PluginConfig } from "./types.js";

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

      const ctxTyped = ctx as { runId?: string };
      const messages = Array.isArray(event.messages) ? event.messages : [];
      const lastMessage = messages.length > 0 ? messages[messages.length - 1] : undefined;
      const query =
        typeof lastMessage === "object" &&
        lastMessage !== null &&
        typeof (lastMessage as { content?: unknown }).content === "string"
          ? (lastMessage as { content: string }).content
          : "";

      const result = await runSidecarCommand(config, "prepare", {
        schema: "nollm.provider.prepare.v1",
        request_id: `prepare-${Date.now()}`,
        agent_id: "main",
        session_id: api.id,
        run_id: ctxTyped.runId ?? `run-${Date.now()}`,
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

      const ctxEnvelope = (result as unknown as { context: MemoryContextEnvelope }).context;
      return { prependContext: formatMemoryContext(ctxEnvelope) };
    }
  );

  api.on(
    "agent_end",
    async (event) => {
      if (!config) {
        return;
      }
      try {
        const result = await runSidecarCommand(config, "capture", {
          schema: "nollm.provider.capture.v1",
          request_id: `capture-${Date.now()}`,
          agent_id: "main",
          session_id: api.id,
          run_id: event.runId ?? `run-${Date.now()}`,
          success: event.success,
          messages: event.messages,
        });
        if (!result.ok) {
          api.logger.warn(`Nollm capture failed: ${result.error.message}`);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        api.logger.warn(`Nollm capture exception: ${message}`);
      }
    }
  );
}
