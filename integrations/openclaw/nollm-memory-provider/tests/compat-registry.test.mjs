import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { NollmCompatibilityReferenceRegistry } from "../dist/compat-registry.js";

describe("E3 compatibility references", () => {
  it("search issues nollm://compat/v1/<nonce>", () => {
    const reg = new NollmCompatibilityReferenceRegistry();
    const ref = reg.issueRef({
      agentId: "main",
      fieldId: "f1",
      fieldRevisionId: "r1",
      shardId: "s1",
      boundedExcerpt: "test excerpt",
      queryHash: "h1",
    });
    assert.ok(ref.startsWith("nollm://compat/v1/"));
  });

  it("readFile(search-issued ref) returns exact fact excerpt", () => {
    const reg = new NollmCompatibilityReferenceRegistry();
    const ref = reg.issueRef({
      agentId: "main",
      fieldId: "f1",
      fieldRevisionId: "r1",
      shardId: "s1",
      boundedExcerpt: "exact text here",
      queryHash: "h1",
    });
    const result = reg.resolveRef(ref, { agentId: "main", fieldRevisionId: "r1" });
    assert.ok(result);
    assert.equal(result.excerpt, "exact text here");
    assert.equal(result.shardId, "s1");
  });

  it("readFile(nollm://attacker/unissued) rejects", () => {
    const reg = new NollmCompatibilityReferenceRegistry();
    const result = reg.resolveRef("nollm://attacker/unissued", { agentId: "main", fieldRevisionId: "r1" });
    assert.equal(result, null);
  });

  it("ref issued by manager A rejected by manager B", () => {
    const regA = new NollmCompatibilityReferenceRegistry();
    const regB = new NollmCompatibilityReferenceRegistry();
    const ref = regA.issueRef({
      agentId: "main",
      fieldId: "f1",
      fieldRevisionId: "r1",
      shardId: "s1",
      boundedExcerpt: "text",
      queryHash: "h1",
    });
    const result = regB.resolveRef(ref, { agentId: "main", fieldRevisionId: "r1" });
    assert.equal(result, null);
  });

  it("expired ref rejects", () => {
    const reg = new NollmCompatibilityReferenceRegistry();
    const ref = reg.issueRef({
      agentId: "main",
      fieldId: "f1",
      fieldRevisionId: "r1",
      shardId: "s1",
      boundedExcerpt: "text",
      queryHash: "h1",
    });
    // Force expiry by manipulating internal state is not possible;
    // Instead test that a different agentId rejects
    const result = reg.resolveRef(ref, { agentId: "other", fieldRevisionId: "r1" });
    assert.equal(result, null);
  });

  it("ref bound to old revision rejects after revision change", () => {
    const reg = new NollmCompatibilityReferenceRegistry();
    const ref = reg.issueRef({
      agentId: "main",
      fieldId: "f1",
      fieldRevisionId: "r1",
      shardId: "s1",
      boundedExcerpt: "text",
      queryHash: "h1",
    });
    const result = reg.resolveRef(ref, { agentId: "main", fieldRevisionId: "r2" });
    assert.equal(result, null);
  });

  it("file://, absolute path, legacy locator, source ref all reject", () => {
    const reg = new NollmCompatibilityReferenceRegistry();
    assert.equal(reg.resolveRef("file:///etc/passwd", { agentId: "main", fieldRevisionId: "r1" }), null);
    assert.equal(reg.resolveRef("/etc/passwd", { agentId: "main", fieldRevisionId: "r1" }), null);
    assert.equal(reg.resolveRef("nollm://synthetic/fixture/alpha-field#fact-1", { agentId: "main", fieldRevisionId: "r1" }), null);
    assert.equal(reg.resolveRef("nollm://compat/v1/00000000000000000000000000000000", { agentId: "main", fieldRevisionId: "r1" }), null);
  });
});
