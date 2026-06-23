import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { listFiles, makeMockApi, makeProviderConfig, makeTempDir } from "./helpers.mjs";
import { createNollmProvider } from "../dist/provider.js";

const PROHIBITED_TOOLS = [
  "memory_search",
  "memory_get",
  "memory_store",
  "memory_recall",
  "nollm_field_overview",
  "nollm_open_well",
  "nollm_surface",
  "nollm_focus",
  "nollm_drift",
  "nollm_read",
  "nollm_recall_trace",
];

describe("F0-03 Primary tool catalog excludes prohibited tools", () => {
  it("manifest declares empty contracts.tools", () => {
    const manifest = JSON.parse(
      fs.readFileSync(
        path.resolve(import.meta.dirname, "..", "openclaw.plugin.json"),
        "utf8"
      )
    );
    assert.deepEqual(manifest.contracts?.tools, []);
  });

  it("provider never calls registerTool", () => {
    const api = makeMockApi(makeProviderConfig(makeTempDir()));
    let toolRegistered = false;
    api.registerTool = () => {
      toolRegistered = true;
    };
    createNollmProvider(api);
    assert.equal(toolRegistered, false);
  });

  it("provider entry uses memory capability registration, not tool plugin", () => {
    const providerSource = fs.readFileSync(
      path.resolve(import.meta.dirname, "..", "dist", "provider.js"),
      "utf8"
    );
    assert.ok(providerSource.includes("registerMemoryCapability"));
    assert.ok(!providerSource.includes("defineToolPlugin"));
  });

  it("provider source does not register prohibited tool names", () => {
    const srcFiles = listFiles(
      path.resolve(import.meta.dirname, "..", "src"),
      ".ts"
    );
    for (const file of srcFiles) {
      const text = fs.readFileSync(file, "utf8");
      for (const name of PROHIBITED_TOOLS) {
        assert.ok(
          !text.includes(name),
          `${path.basename(file)} contains prohibited tool name: ${name}`
        );
      }
    }
  });
});
