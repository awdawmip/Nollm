import type { MemoryContextEnvelope } from "./types.js";

export function formatMemoryContext(envelope: MemoryContextEnvelope): string {
  const lines: string[] = ["NOLLM_MEMORY_CONTEXT_V1"];
  lines.push("memory_persistence_rule: Do not claim that a current-turn fact has been permanently remembered, written, or persisted unless it already appears as a returned Nollm native memory in this context. Capture happens after the response and may fail.");
  lines.push(`freshness: ${envelope.freshness}`);
  if (envelope.facts && envelope.facts.length > 0) {
    lines.push("facts:");
    for (const fact of envelope.facts) {
      lines.push(`- [${fact.kind}] ${fact.claim}`);
    }
  }
  if (envelope.explicit_absences && envelope.explicit_absences.length > 0) {
    lines.push("explicit_absences:");
    for (const absence of envelope.explicit_absences) {
      lines.push(`- ${absence}`);
    }
  }
  if (envelope.warnings && envelope.warnings.length > 0) {
    lines.push("warnings:");
    for (const warning of envelope.warnings) {
      lines.push(`- ${warning}`);
    }
  }
  if (envelope.boundaries && envelope.boundaries.length > 0) {
    lines.push("boundaries:");
    for (const boundary of envelope.boundaries) {
      lines.push(`- ${JSON.stringify(boundary)}`);
    }
  }
  lines.push("END_NOLLM_MEMORY_CONTEXT_V1");
  return lines.join("\n");
}

export function makeUnavailableBoundary(): string {
  return [
    "NOLLM_MEMORY_CONTEXT_V1",
    "memory_persistence_rule: Do not claim that a current-turn fact has been permanently remembered, written, or persisted unless it already appears as a returned Nollm native memory in this context. Capture happens after the response and may fail.",
    "freshness: unavailable",
    "explicit_absences:",
    "- Nollm active memory is unavailable for this turn.",
    "END_NOLLM_MEMORY_CONTEXT_V1",
  ].join("\n");
}
