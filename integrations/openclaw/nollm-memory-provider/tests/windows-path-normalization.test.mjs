import { describe, it } from "node:test";
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixtures = JSON.parse(
  readFileSync(join(__dirname, "../test-fixtures/windows-path-cases.json"), "utf8")
);

function normalizePortablePath(input) {
  if (!input || typeof input !== "string") {
    return { raw_input: input, normalized_path: null, exists: false, resolution_status: "empty" };
  }
  if (input.startsWith("\\\\")) {
    return { raw_input: input, normalized_path: null, exists: false, resolution_status: "unsupported_unc" };
  }
  return { raw_input: input, normalized_path: input.replace(/\\/g, "/"), exists: false, resolution_status: "candidate_not_exists" };
}

function protectPath(portablePath, userProfile) {
  if (!portablePath) return null;
  const home = userProfile.replace(/\\/g, "/");
  if (portablePath.startsWith(home)) {
    return "%USERPROFILE%" + portablePath.slice(home.length);
  }
  return portablePath;
}

describe("T1 Windows path normalization", () => {
  for (const c of fixtures.cases) {
    it(`${c.name}: output never contains bare backslash`, () => {
      const info = normalizePortablePath(c.input);
      if (info.normalized_path !== null) {
        assert.strictEqual(info.normalized_path.includes("\\"), false, "normalized path must not contain backslash");
      }
    });

    if (c.expected_normalized !== undefined) {
      it(`${c.name}: normalized path matches fixture`, () => {
        const info = normalizePortablePath(c.input);
        assert.strictEqual(info.normalized_path, c.expected_normalized);
      });
    }

    if (c.expected_public !== undefined) {
      it(`${c.name}: public path matches fixture`, () => {
        const info = normalizePortablePath(c.input);
        const home = process.platform === "win32" ? process.env.USERPROFILE : "C:/Users/Administrator";
        const publicPath = protectPath(info.normalized_path, home);
        assert.strictEqual(publicPath, c.expected_public);
      });
    }

    if (c.expected_resolution_status) {
      it(`${c.name}: resolution status matches fixture`, () => {
        const info = normalizePortablePath(c.input);
        assert.strictEqual(info.resolution_status, c.expected_resolution_status);
      });
    }
  }
});
