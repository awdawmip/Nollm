import type { MemoryContextEnvelope, SidecarResult } from "./types.js";
import { sidecarFailure } from "./errors.js";
import { formatMemoryContext } from "./hook-context.js";

const MAX_WARNINGS = 10;
const MAX_BOUNDARIES = 10;
const MAX_ABSENCES = 10;
const MAX_WARNING_LEN = 500;
const MAX_BOUNDARY_JSON_LEN = 1000;
const MAX_ABSENCE_LEN = 500;

export function validatePrepareResult(
  result: SidecarResult,
  config: { maxFacts: number; maxContextCharacters: number }
): SidecarResult | { ok: true; schema: "nollm.provider.prepare.v2"; context: MemoryContextEnvelope } {
  if (!result.ok) {
    return result;
  }

  const raw = result as Record<string, unknown>;

  if (raw.schema !== "nollm.provider.prepare.v2") {
    return sidecarFailure("sidecar_failed", "prepare result schema mismatch", false);
  }

  const context = raw.context;
  if (!context || typeof context !== "object") {
    return sidecarFailure("sidecar_failed", "missing context in prepare result", false);
  }

  const validated = validateContextEnvelope(context, config);
  if (!validated) {
    return sidecarFailure("sidecar_failed", "context envelope validation failed", false);
  }

  const finalRendered = formatMemoryContext(validated);
  if (finalRendered.length > config.maxContextCharacters) {
    return sidecarFailure("sidecar_failed", "rendered context exceeds total budget after trimming", false);
  }

  return { ok: true, schema: "nollm.provider.prepare.v2", context: validated };
}

export function validateContextEnvelope(
  context: unknown,
  config: { maxFacts: number; maxContextCharacters: number }
): MemoryContextEnvelope | null {
  if (!context || typeof context !== "object") {
    return null;
  }
  const c = context as Record<string, unknown>;

  if (c.schema !== "NOLLM_MEMORY_CONTEXT_V1") return null;

  const freshness = c.freshness;
  if (freshness !== "fresh" && freshness !== "none" && freshness !== "unavailable") {
    return null;
  }

  if (!Array.isArray(c.facts)) return null;
  if (!Array.isArray(c.boundaries)) return null;
  if (!Array.isArray(c.warnings) || !c.warnings.every((w) => typeof w === "string")) {
    return null;
  }
  if (!Array.isArray(c.explicit_absences) || !c.explicit_absences.every((e) => typeof e === "string")) {
    return null;
  }

  const validatedFacts: Array<{ memory_id: string; claim: string; kind: string; source: string; revision_id?: string }> = [];
  for (const fact of c.facts) {
    if (!fact || typeof fact !== "object") return null;
    const f = fact as Record<string, unknown>;
    if (typeof f.memory_id !== "string" || !f.memory_id) return null;
    if (typeof f.claim !== "string" || !f.claim) return null;
    if (typeof f.kind !== "string" || !f.kind) return null;
    if (typeof f.source !== "string" || !f.source) return null;
    validatedFacts.push({
      memory_id: f.memory_id,
      claim: f.claim,
      kind: f.kind,
      source: f.source,
      revision_id: typeof f.revision_id === "string" ? f.revision_id : undefined,
    });
  }

  // Sidecar fresh with zero facts is invalid; none/unavailable must have zero facts.
  if (freshness === "fresh" && validatedFacts.length === 0) return null;
  if ((freshness === "none" || freshness === "unavailable") && validatedFacts.length > 0) return null;

  const trimmedWarnings = (c.warnings as string[])
    .slice(0, MAX_WARNINGS)
    .map((w) => w.slice(0, MAX_WARNING_LEN));

  const trimmedBoundaries = (c.boundaries as Array<Record<string, unknown>>)
    .slice(0, MAX_BOUNDARIES)
    .map((b) => {
      const json = JSON.stringify(b);
      if (json.length > MAX_BOUNDARY_JSON_LEN) {
        return { truncated: true, original_length: json.length };
      }
      return b;
    });

  const trimmedAbsences = (c.explicit_absences as string[])
    .slice(0, MAX_ABSENCES)
    .map((e) => e.slice(0, MAX_ABSENCE_LEN));

  const slicedFacts = validatedFacts.slice(0, config.maxFacts);

  let finalFreshness = freshness as "fresh" | "none" | "unavailable";
  let finalAbsences = trimmedAbsences;
  if (freshness === "fresh" && slicedFacts.length === 0 && validatedFacts.length > 0) {
    finalFreshness = "none";
    finalAbsences = [
      ...trimmedAbsences,
      "Context budget exceeded: facts trimmed to zero.",
    ];
  }

  const envelope: MemoryContextEnvelope = {
    schema: "NOLLM_MEMORY_CONTEXT_V1",
    freshness: finalFreshness,
    facts: slicedFacts,
    boundaries: trimmedBoundaries,
    warnings: trimmedWarnings,
    explicit_absences: finalAbsences,
  };

  const rendered = formatMemoryContext(envelope);
  if (rendered.length > config.maxContextCharacters) {
    while (envelope.facts.length > 0 && rendered.length > config.maxContextCharacters) {
      envelope.facts.pop();
      if (envelope.facts.length === 0) {
        envelope.freshness = "none";
        envelope.explicit_absences = [
          ...finalAbsences,
          "Context budget exceeded: all facts removed to fit within total context limit.",
        ];
      }
      const reRendered = formatMemoryContext(envelope);
      if (reRendered.length <= config.maxContextCharacters) {
        return envelope;
      }
    }
    if (formatMemoryContext(envelope).length > config.maxContextCharacters) {
      return null;
    }
  }

  return envelope;
}

export function validateCaptureResult(result: SidecarResult): boolean {
  if (!result.ok) return false;
  const raw = result as Record<string, unknown>;
  if (raw.schema !== "nollm.active_memory_capture.v1") return false;
  const capture = raw.capture;
  if (!capture || typeof capture !== "object") return false;
  const cap = capture as Record<string, unknown>;
  return (
    typeof cap.event_id === "string" &&
    typeof cap.promoted_count === "number" &&
    typeof cap.deduplicated_count === "number" &&
    typeof cap.suppressed_count === "number" &&
    typeof cap.rejected_count === "number" &&
    Array.isArray(cap.records)
  );
}
