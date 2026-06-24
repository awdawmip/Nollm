import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { validatePrepareResult, validateContextEnvelope } from "../dist/context-validation.js";

describe("E1 context validation / budget", () => {
  it("malformed prepare result schema -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "wrong.result", context: {} },
      { maxFacts: 3, maxCharacters: 1200 }
    );
    assert.equal(result.ok, false);
  });

  it("wrong context schema -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "evil.context.v9" } },
      { maxFacts: 3, maxCharacters: 1200 }
    );
    assert.equal(result.ok, false);
  });

  it("facts not array -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "fresh", facts: "notarray", boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } } },
      { maxFacts: 3, maxCharacters: 1200 }
    );
    assert.equal(result.ok, false);
  });

  it("warnings wrong type -> unavailable", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "none", facts: [], boundaries: [], warnings: "notarray", completeness: { mode: "bounded", explicit_absences: [] } } },
      { maxFacts: 3, maxCharacters: 1200 }
    );
    assert.equal(result.ok, false);
  });

  it("50 x 5000-char sidecar facts -> no oversized prompt", () => {
    const bigFacts = (i) => ({
      shard_id: `s${i}`,
      claim: "x".repeat(5000),
      epistemic_state: "source_backed",
      operational_state: "active",
      source_refs: ["nollm://synthetic/f#1"],
    });
    const facts = Array.from({ length: 50 }, (_, i) => bigFacts(i));
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "fresh", facts, boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } } },
      { maxFacts: 3, maxCharacters: 1200 }
    );
    assert.equal(result.ok, true);
    const ctx = result.context;
    assert.ok(ctx.facts.length <= 3, "maxFacts must be honored");
    const totalLen = JSON.stringify(ctx).length;
    assert.ok(totalLen <= 1200 + 512, "total must not exceed budget + overhead");
  });

  it("second-layer maxFacts honored", () => {
    const facts = Array.from({ length: 10 }, (_, i) => ({
      shard_id: `s${i}`,
      claim: `claim ${i}`,
      epistemic_state: "source_backed",
      operational_state: "active",
      source_refs: ["r"],
    }));
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "fresh", facts, boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } } },
      { maxFacts: 2, maxCharacters: 10000 }
    );
    assert.equal(result.context.facts.length, 2);
  });

  it("second-layer maxCharacters honored", () => {
    const facts = Array.from({ length: 5 }, (_, i) => ({
      shard_id: `s${i}`,
      claim: "y".repeat(400),
      epistemic_state: "source_backed",
      operational_state: "active",
      source_refs: ["r"],
    }));
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "fresh", facts, boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } } },
      { maxFacts: 20, maxCharacters: 800 }
    );
    const totalLen = JSON.stringify(result.context).length;
    assert.ok(totalLen <= 800 + 512, "must respect maxCharacters + overhead");
  });

  it("no raw malformed sidecar JSON is injected", () => {
    const result = validatePrepareResult(
      { ok: true, schema: "nollm.provider.prepare_result.v1", context: { schema: "evil", evil: true } },
      { maxFacts: 3, maxCharacters: 1200 }
    );
    assert.equal(result.ok, false);
  });

  it("fresh/none/unavailable state consistency", () => {
    // fresh with 0 facts -> fail
    assert.equal(validateContextEnvelope(
      { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "fresh", facts: [], boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } },
      { maxFacts: 3, maxCharacters: 1200 }
    ), null);

    // none with facts -> fail
    assert.equal(validateContextEnvelope(
      { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "none", facts: [{ shard_id: "s1", claim: "c", epistemic_state: "x", operational_state: "y", source_refs: ["r"] }], boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } },
      { maxFacts: 3, maxCharacters: 1200 }
    ), null);

    // none with 0 facts -> ok
    assert.ok(validateContextEnvelope(
      { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "none", facts: [], boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } },
      { maxFacts: 3, maxCharacters: 1200 }
    ));

    // unavailable with 0 facts -> ok
    assert.ok(validateContextEnvelope(
      { schema: "nollm.memory_context.v1", context_id: "c1", field_id: "f1", field_revision_id: "r1", freshness: "unavailable", facts: [], boundaries: [], warnings: [], completeness: { mode: "bounded", explicit_absences: [] } },
      { maxFacts: 3, maxCharacters: 1200 }
    ));
  });
});
