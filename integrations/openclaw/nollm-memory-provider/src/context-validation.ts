import type { MemoryContextEnvelope, SidecarResult } from "./types.js";
import { sidecarFailure } from "./errors.js";

const HEADER_OVERHEAD = 512;

export function validatePrepareResult(
  result: SidecarResult,
  config: { maxFacts: number; maxCharacters: number }
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

  return { ok: true, schema: "nollm.provider.prepare_result.v1", context: validated };
}

export function validateContextEnvelope(
  context: unknown,
  config: { maxFacts: number; maxCharacters: number }
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

  // Secondary budget enforcement
  const maxFacts = config.maxFacts;
  const maxChars = config.maxCharacters;
  const slicedFacts = validatedFacts.slice(0, maxFacts);

  let totalChars = HEADER_OVERHEAD;
  const budgetFacts: Array<Record<string, unknown>> = [];
  for (const fact of slicedFacts) {
    const factJson = JSON.stringify(fact);
    const factChars = factJson.length;
    if (totalChars + factChars > maxChars) {
      break;
    }
    totalChars += factChars;
    budgetFacts.push(fact);
  }

  const envelope: MemoryContextEnvelope = {
    schema: "nollm.memory_context.v1",
    context_id: c.context_id as string,
    field_id: c.field_id as string,
    field_revision_id: c.field_revision_id as string,
    freshness: freshness as "fresh" | "none" | "unavailable",
    facts: budgetFacts,
    boundaries: c.boundaries as Array<Record<string, unknown>>,
    warnings: c.warnings as string[],
    completeness: {
      mode: "bounded",
      explicit_absences: comp.explicit_absences as string[],
    },
  };

  return envelope;
}
