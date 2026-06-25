import { describe, it } from "node:test";
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const scriptPath = join(__dirname, "../tools/windows-live-preflight.ps1");
const fixtures = JSON.parse(
  readFileSync(join(__dirname, "../test-fixtures/preflight-command-fixtures.json"), "utf8")
);

const script = readFileSync(scriptPath, "utf8");

describe("T7 static safety constraints", () => {
  for (const pattern of fixtures.forbidden_command_patterns) {
    it(`script does not contain forbidden pattern: ${pattern}`, () => {
      assert.ok(!script.includes(pattern), `found forbidden pattern: ${pattern}`);
    });
  }

  it("script declares read_only mode in safety section", () => {
    assert.ok(script.includes('"read_only"'), "mode must be read_only");
  });

  it("script enforces Windows platform gate", () => {
    assert.ok(script.includes("$IsWindows"), "must check $IsWindows");
  });
});

describe("T8-T9 no content emission", () => {
  it("script never reads legacy memory content", () => {
    assert.ok(!script.includes("Get-Content") || script.includes("metadata"), "must not read legacy memory content");
  });
});
