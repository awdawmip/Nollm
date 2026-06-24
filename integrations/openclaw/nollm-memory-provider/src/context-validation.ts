import type { MemoryContextEnvelope, SidecarResult } from "./types.js";
import { sidecarFailure } from "./errors.js";
import { formatMemoryContext } from "./hook-context.js";

const HEADER_OVERHEAD = 512;
const MAX_WARNINGS = 10;
const MAX_BOUNDARIES = 10;
const MAX_ABSENCES = 10;
const MAX_WARNING_LEN = 500;
const MAX_BOUNDARY_JSON_LEN = 1000;
const MAX_ABSENCE_LEN = 500;

export function validatePrepareResult(
  result: SidecarResult,
  config: { maxFacts: number; maxCharacters: number; maxContextCharacters: number }
): SidecarResult {
  if (!result.ok) {
    return result;
  }

  const raw = result as Record<string, unknown>;

  if (raw.schema !== "nollm.provider.prepare_result.v1") {
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

  // D2: verify total rendered context is within budget
  const rendered = formatMemoryContext(validated);
  if (rendered.length > config.maxContextCharacters) {
    return sidecarFailure("sidecar_failed", "rendered context exceeds total budget after trimming", false);
  }

  return { ok: true, schema: "nollm.provider.prepare_result.v1", context: validated };
}

export function validateContextEnvelope(
  context: unknown,
  config: { maxFacts: number; maxCharacters: number; maxContextCharacters: number }
): MemoryContextEnvelope | null {
  if (!context || typeof context !== "object") {
    return null;
  }
  const c = context as Record<string, unknown>;

  if (c.schema !== "nollm.memory_context.v1") return null;
  if (typeof c.context_id !== "string" || !c.context_id) return null;
  if (typeof c.field_id !== "string" || !c.field_id) return null;
  if (typeof c.field_revision_id !== "string" || !c.field_revision_id) return null;

  const freshness = c.freshness;
  if (freshness !== "fresh" && freshness !== "none" && freshness !== "unavailable") {
    return null;
  }

  if (!Array.isArray(c.facts)) return null;
  if (!Array.isArray(c.boundaries)) return null;
  if (!Array.isArray(c.warnings) || !c.warnings.every((w) => typeof w === "string")) {
    return null;
  }

  const completeness = c.completeness;
  if (!completeness || typeof completeness !== "object") return null;
  const comp = completeness as Record<string, unknown>;
  if (comp.mode !== "bounded") return null;
  if (!Array.isArray(comp.explicit_absences) || !comp.explicit_absences.every((e) => typeof e === "string")) {
    return null;
  }

  // freshness=fresh requires at least one fact
  if (freshness === "fresh" && c.facts.length === 0) return null;
  // freshness=none/unavailable requires empty facts
  if ((freshness === "none" || freshness === "unavailable") && c.facts.length > 0) return null;

  // Validate each fact has required fields
  const validatedFacts: Array<Record<string, unknown>> = [];
  for (const fact of c.facts) {
    if (!fact || typeof fact !== "object") return null;
    const f = fact as Record<string, unknown>;
    if (typeof f.shard_id !== "string" || !f.shard_id) return null;
    if (typeof f.claim !== "string" || !f.claim) return null;
    if (typeof f.epistemic_state !== "string" || !f.epistemic_state) return null;
    if (typeof f.operational_state !== "string" || !f.operational_state) return null;
    if (!Array.isArray(f.source_refs)) return null;
    validatedFacts.push(f);
  }

  // D2: Trim warnings, boundaries, explicit_absences to bounded counts and lengths
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

  const trimmedAbsences = (comp.explicit_absences as string[])
    .slice(0, MAX_ABSENCES)
    .map((e) => e.slice(0, MAX_ABSENCE_LEN));

  // Secondary budget enforcement on facts
  const maxFacts = config.maxFacts;
  const maxChars = config.maxCharacters;
  const slicedFacts = validatedFacts.slice(0, maxFacts);

  let factChars = 0;
  const budgetFacts: Array<Record<string, unknown>> = [];
  for (const fact of slicedFacts) {
    const factJson = JSON.stringify(fact);
    if (factChars + factJson.length > maxChars && budgetFacts.length > 0) {
      break;
    }
    factChars += factJson.length;
    budgetFacts.push(fact);
  }

  // D2: If all facts were trimmed away but freshness was fresh, degrade to none
  let finalFreshness = freshness as "fresh" | "none" | "unavailable";
  let finalAbsences = trimmedAbsences;
  if (freshness === "fresh" && budgetFacts.length === 0) {
    finalFreshness = "none";
    finalAbsences = [
      ...trimmedAbsences,
      "Context budget exceeded: facts trimmed to zero. Memory may exist but could not be rendered within limits.",
    ];
  }

  // D2: Check total rendered context against maxContextCharacters
  const envelope: MemoryContextEnvelope = {
    schema: "nollm.memory_context.v1",
    context_id: c.context_id as string,
    field_id: c.field_id as string,
    field_revision_id: c.field_revision_id as string,
    freshness: finalFreshness,
    facts: budgetFacts,
    boundaries: trimmedBoundaries,
    warnings: trimmedWarnings,
    completeness: {
      mode: "bounded",
      explicit_absences: finalAbsences,
    },
  };

  // Final total budget check
  const rendered = formatMemoryContext(envelope);
  if (rendered.length > config.maxContextCharacters) {
    // Try reducing facts further
    while (budgetFacts.length > 0 && rendered.length > config.maxContextCharacters) {
      budgetFacts.pop();
      envelope.facts = budgetFacts;
      if (budgetFacts.length === 0) {
        envelope.freshness = "none";
        envelope.completeness.explicit_absences = [
          ...finalAbsences,
          "Context budget exceeded: all facts removed to fit within total context limit.",
        ];
      }
      // Re-check
      const reRendered = formatMemoryContext(envelope);
      if (reRendered.length <= config.maxContextCharacters) {
        return envelope;
      }
    }
    // If still over budget with empty facts, return null (caller emits unavailable)
    if (formatMemoryContext(envelope).length > config.maxContextCharacters) {
      return null;
    }
  }

  return envelope;
}
