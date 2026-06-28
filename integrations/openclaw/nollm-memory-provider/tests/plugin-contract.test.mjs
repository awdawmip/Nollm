import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {
  makeMockApi,
  makeProviderConfig,
  makeTempDir,
  invokePrepare,
} from "./helpers.mjs";
import { createNollmProvider } from "../dist/provider.js";

describe("T1 manifest", () => {
  it("has id nollm, kind memory, and empty contracts.tools", () => {
    const manifest = JSON.parse(
      fs.readFileSync(
        path.resolve(import.meta.dirname, "..", "openclaw.plugin.json"),
        "utf8"
      )
    );
    assert.equal(manifest.id, "nollm");
    assert.equal(manifest.kind, "memory");
    assert.deepEqual(manifest.contracts?.tools, []);
    const required = manifest.configSchema.required;
    assert.ok(required.includes("pythonExecutable"), "requires pythonExecutable");
    assert.ok(required.includes("nativeStoreRoot"), "requires nativeStoreRoot");
    assert.ok(manifest.configSchema.properties.trialId, "declares controller-provided trialId");
    assert.ok(!required.includes("alphaFixturePath"), "no alphaFixturePath");
  });
});

describe("T2-T4 provider registration", () => {
  it("registers memory capability with promptBuilder=[], flushPlanResolver=null, and no active runtime", () => {
    const api = makeMockApi(makeProviderConfig(makeTempDir()));
    createNollmProvider(api);
    assert.ok(api._events.capability, "capability should be registered");
    assert.deepEqual(api._events.capability.promptBuilder(), []);
    assert.equal(api._events.capability.flushPlanResolver(), null);
    assert.equal(api._events.capability.runtime, undefined, "compatibility runtime must not be exposed in W2");
  });

  it("registers agent_turn_prepare and agent_end handlers", () => {
    const api = makeMockApi(makeProviderConfig(makeTempDir()));
    createNollmProvider(api);
    assert.equal(api._events["agent_turn_prepare"]?.length, 1);
    assert.equal(api._events["agent_end"]?.length, 1);
  });

  it("registers zero Primary-visible tools", () => {
    const api = makeMockApi(makeProviderConfig(makeTempDir()));
    let toolRegistered = false;
    api.registerTool = () => {
      toolRegistered = true;
    };
    createNollmProvider(api);
    assert.equal(toolRegistered, false, "registerTool should not be called");
    assert.equal(api._events.tools, undefined);
  });

  it("returns unavailable boundary when config is missing", async () => {
    const api = makeMockApi({});
    createNollmProvider(api);
    const result = await invokePrepare(
      api,
      { messages: [{ role: "user", content: "hello" }] },
      {}
    );
    assert.ok(result.prependContext.includes("NOLLM_MEMORY_CONTEXT_V1"));
    assert.ok(result.prependContext.includes("unavailable"));
  });
});
