import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { extractLatestUserText, resolveNollmTurnIdentity } from "../dist/identity.js";

describe("E2 query and identity", () => {
  it("user then assistant -> use user text", () => {
    const msgs = [
      { role: "user", content: "Please remember blue labels" },
      { role: "assistant", content: "Okay, I will help." },
    ];
    assert.equal(extractLatestUserText(msgs), "Please remember blue labels");
  });

  it("text-block array user content -> use joined user text", () => {
    const msgs = [
      { role: "user", content: [{ text: "hello" }, { text: "world" }] },
    ];
    assert.equal(extractLatestUserText(msgs), "hello\nworld");
  });

  it("no user message -> empty string", () => {
    const msgs = [
      { role: "assistant", content: "I can help." },
      { role: "system", content: "system prompt" },
    ];
    assert.equal(extractLatestUserText(msgs), "");
  });

  it("ctx.agentId/sessionId/runId forwarded", () => {
    const result = resolveNollmTurnIdentity({
      agentId: "agent-1",
      sessionId: "sess-1",
      runId: "run-1",
    });
    assert.equal(result.agentId, "agent-1");
    assert.equal(result.sessionId, "sess-1");
    assert.equal(result.runId, "run-1");
    assert.equal(result.warnings.length, 0);
  });

  it("different sessions do not share emitted identity", () => {
    const r1 = resolveNollmTurnIdentity({ agentId: "a", sessionId: "s1", runId: "r1" });
    const r2 = resolveNollmTurnIdentity({ agentId: "a", sessionId: "s2", runId: "r2" });
    assert.notEqual(r1.sessionId, r2.sessionId);
  });

  it("configured unsupported agent -> explicit rejection", () => {
    const result = resolveNollmTurnIdentity(
      { agentId: "other", sessionId: "s", runId: "r" },
      { allowAgentIds: ["main"] }
    );
    assert.ok(result.warnings.some((w) => w.includes("agent_id_rejected")));
    assert.equal(result.sessionId, "");
  });

  it("fallback identity has warnings", () => {
    const result = resolveNollmTurnIdentity({});
    assert.ok(result.warnings.length > 0);
    assert.equal(result.agentId, "main");
  });
});
