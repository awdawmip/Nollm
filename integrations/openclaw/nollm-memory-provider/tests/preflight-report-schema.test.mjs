import { describe, it } from "node:test";
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const schema = JSON.parse(
  readFileSync(join(__dirname, "../tools/preflight-report-schema.json"), "utf8")
);

function validateReport(report) {
  const errors = [];
  if (report.schema !== schema.properties.schema.const) {
    errors.push(`schema must be ${schema.properties.schema.const}`);
  }
  for (const key of schema.required) {
    if (!(key in report)) errors.push(`missing required field: ${key}`);
  }
  if (report.safety) {
    for (const [k, v] of Object.entries(schema.properties.safety.properties)) {
      if (v.const !== undefined && report.safety[k] !== v.const) {
        errors.push(`safety.${k} must be ${v.const}`);
      }
    }
  }
  if (report.platform?.os !== "Windows") {
    errors.push("platform.os must be Windows");
  }
  if (report.readiness) {
    const statuses = ["ready", "blocked", "unknown"];
    for (const key of ["p1_node_only_probe", "p2_managed_python_probe"]) {
      const status = report.readiness[key]?.status;
      if (!statuses.includes(status)) errors.push(`readiness.${key}.status invalid: ${status}`);
    }
  }
  return errors;
}

describe("T5 report schema validation", () => {
  it("accepts a synthetic valid report", () => {
    const report = {
      schema: "nollm.windows_openclaw_preflight.v1",
      generated_at: new Date().toISOString(),
      platform: { os: "Windows", powershell_version: "7.5.0", node: { status: "unavailable", notes: [] } },
      safety: {
        mode: "read_only",
        config_modified: false,
        gateway_restarted: false,
        plugin_installed_or_linked: false,
        nollm_python_started: false,
        legacy_memory_content_emitted: false,
        transcript_content_emitted: false
      },
      openclaw: { cli: {}, profile: {}, config: {}, state: {}, plugins: {}, memory: {}, sessions: {} },
      workspace: { path: {}, legacy_memory_metadata: {}, bootstrap_risk: {} },
      python: { interactive_shell: { candidates: [] }, gateway_environment: {} },
      gateway_process: {},
      readiness: {
        p1_node_only_probe: { status: "ready", blocking_reasons: [] },
        p2_managed_python_probe: { status: "blocked", blocking_reasons: ["p1_not_ready"] }
      },
      operator_private_paths: {},
      unknowns: [],
      commands: []
    };
    const errors = validateReport(report);
    assert.deepStrictEqual(errors, [], errors.join("; "));
  });

  it("rejects unsafe safety booleans", () => {
    const report = {
      schema: "nollm.windows_openclaw_preflight.v1",
      generated_at: new Date().toISOString(),
      platform: { os: "Windows", powershell_version: "7.5.0", node: { status: "unavailable", notes: [] } },
      safety: {
        mode: "read_only",
        config_modified: true,
        gateway_restarted: false,
        plugin_installed_or_linked: false,
        nollm_python_started: false,
        legacy_memory_content_emitted: false,
        transcript_content_emitted: false
      },
      openclaw: { cli: {}, profile: {}, config: {}, state: {}, plugins: {}, memory: {}, sessions: {} },
      workspace: { path: {}, legacy_memory_metadata: {}, bootstrap_risk: {} },
      python: { interactive_shell: { candidates: [] }, gateway_environment: {} },
      gateway_process: {},
      readiness: {
        p1_node_only_probe: { status: "ready", blocking_reasons: [] },
        p2_managed_python_probe: { status: "blocked", blocking_reasons: [] }
      },
      operator_private_paths: {},
      unknowns: [],
      commands: []
    };
    const errors = validateReport(report);
    assert.ok(errors.length > 0, "should detect unsafe safety booleans");
  });
});
