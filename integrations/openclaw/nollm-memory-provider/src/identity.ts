export interface HookContext {
  agentId?: string;
  sessionId?: string;
  sessionKey?: string;
  runId?: string;
}

export interface TurnMessage {
  role?: string;
  content?: unknown;
}

export function extractLatestUserText(messages: TurnMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (!msg || msg.role !== "user") continue;

    const content = msg.content;
    if (typeof content === "string") {
      return content;
    }
    if (Array.isArray(content)) {
      const parts: string[] = [];
      for (const part of content) {
        if (part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string") {
          parts.push((part as Record<string, string>).text);
        }
      }
      if (parts.length > 0) {
        return parts.join("\n");
      }
    }
  }
  return "";
}

export function resolveNollmTurnIdentity(
  ctx: HookContext,
  config?: { allowAgentIds?: string[] }
): {
  agentId: string;
  sessionId: string;
  runId: string;
  warnings: string[];
} {
  const warnings: string[] = [];

  let agentId = ctx.agentId;
  if (!agentId) {
    agentId = "main";
    warnings.push("agent_id_fallback: ctx.agentId missing, using default 'main'");
  }

  if (config?.allowAgentIds && config.allowAgentIds.length > 0) {
    if (!config.allowAgentIds.includes(agentId)) {
      return {
        agentId,
        sessionId: "",
        runId: "",
        warnings: [`agent_id_rejected: '${agentId}' not in allowAgentIds`],
      };
    }
  }

  // D3: fail-close durable identity. No Date.now fallbacks that make context
  // non-reproducible. Missing session/run is a warning, and callers must
  // degrade to unavailable/no-capture if identity is incomplete.
  const sessionId = ctx.sessionId || ctx.sessionKey || "";
  if (!sessionId) {
    warnings.push("session_id_missing: ctx.sessionId/sessionKey missing");
  }

  const runId = ctx.runId || "";
  if (!runId) {
    warnings.push("run_id_missing: ctx.runId missing");
  }

  return { agentId, sessionId, runId, warnings };
}
