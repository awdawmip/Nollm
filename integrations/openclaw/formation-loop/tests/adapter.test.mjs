import test from "node:test"; import assert from "node:assert/strict"; import fs from "node:fs";
test("plugin exposes only explicit formation tool", () => { const manifest=JSON.parse(fs.readFileSync(new URL("../openclaw.plugin.json", import.meta.url))); assert.deepEqual(manifest.contracts.tools,["nollm_form_statement"]); assert.equal(manifest.kind,undefined); });
