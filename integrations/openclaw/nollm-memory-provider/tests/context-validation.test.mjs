import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { validatePrepareResult, validateContextEnvelope } from "../dist/context-validation.js";

describe("E1 context validation / budget", () => {
  it("malformed prepare result schema -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "wrong.result", context: {} },
      { maxFacts: 4, maxContextCharacters: 1400 }
    );
    assert.equal(result.ok, false);
  });

  it("wrong context schema -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "evil.context.v9" } },
      { maxFacts: 4, maxContextCharacters: 1400 }
    );
    assert.equal(result.ok, false);
  });

  it("facts not array -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "fresh", facts: "notarray", boundaries: [], warnings: [], explicit_absences: [] } },
      { maxFacts: 4, maxContextCharacters: 1400 }
    );
    assert.equal(result.ok, false);
  });

  it("warnings wrong type -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "none", facts: [], boundaries: [], warnings: "notarray", explicit_absences: [] } },
      { maxFacts: 4, maxContextCharacters: 1400 }
    );
    assert.equal(result.ok, false);
  });

  it("50 x 5000-char sidecar facts -> no oversized prompt", () => {
    const bigFacts = (i) => ({
      memory_id: `nmem_${i}`,
      claim: "x".repeat(5000),
      kind: "note",
      source: "nollm_native_companion",
    });
    const facts = Array.from({ length: 50 }, (_, i) => bigFacts(i));
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "fresh", facts, boundaries: [], warnings: [], explicit_absences: [] } },
      { maxFacts: 4, maxContextCharacters: 1400 }
    );
    assert.equal(result.ok, true);
    assert.ok(result.context.facts.length <= 4, "maxFacts must be honored");
  });

  it("second-layer maxFacts honored", () => {
    const facts = Array.from({ length: 10 }, (_, i) => ({
      memory_id: `nmem_${i}`,
      claim: `claim ${i}`,
      kind: "note",
      source: "nollm_native_companion",
    }));
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "fresh", facts, boundaries: [], warnings: [], explicit_absences: [] } },
      { maxFacts: 2, maxContextCharacters: 4000 }
    );
    assert.equal(result.context.facts.length, 2);
  });

  it("rendered context stays within maxContextCharacters", () => {
    const facts = Array.from({ length: 5 }, (_, i) => ({
      memory_id: `nmem_${i}`,
      claim: "y".repeat(400),
      kind: "note",
      source: "nollm_native_companion",
    }));
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "fresh", facts, boundaries: [], warnings: [], explicit_absences: [] } },
      { maxFacts: 20, maxContextCharacters: 800 }
    );
    const rendered = JSON.stringify(result.context);
    assert.ok(rendered.length <= 1400, "must respect maxContextCharacters");
  });

  it("no raw malformed sidecar JSON is injected", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare.v2", context: { schema: "evil", evil: true } },
      { maxFacts: 4, maxContextCharacters: 1400 }
    );
    assert.equal(result.ok, false);
  });

  it("fresh/none/unavailable state consistency", () => {
    assert.equal(validateContextEnvelope(
      { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "fresh", facts: [], boundaries: [], warnings: [], explicit_absences: [] },
      { maxFacts: 4, maxContextCharacters: 1400 }
    ), null);

    assert.equal(validateContextEnvelope(
      { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "none", facts: [{ memory_id: "nmem_1", claim: "c", kind: "note", source: "s" }], boundaries: [], warnings: [], explicit_absences: [] },
      { maxFacts: 4, maxContextCharacters: 1400 }
    ), null);

    assert.ok(validateContextEnvelope(
      { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "none", facts: [], boundaries: [], warnings: [], explicit_absences: [] },
      { maxFacts: 4, maxContextCharacters: 1400 }
    ));

    assert.ok(validateContextEnvelope(
      { schema: "NOLLM_MEMORY_CONTEXT_V1", freshness: "unavailable", facts: [], boundaries: [], warnings: [], explicit_absences: [] },
      { maxFacts: 4, maxContextCharacters: 1400 }
    ));
  });
});
