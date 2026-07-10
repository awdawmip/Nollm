import test from "node:test";
import assert from "node:assert/strict";
import manifest from "../openclaw.plugin.json" with { type: "json" };

test("declares the six native tools", () => assert.deepEqual(manifest.contracts.tools, ["nollm_capture", "nollm_prepare_placement", "nollm_apply_placement", "nollm_recall", "nollm_show_source", "nollm_status"]));
