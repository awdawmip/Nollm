import { describe, it } from "node:test";
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixtures = JSON.parse(
  readFileSync(join(__dirname, "../test-fixtures/redaction-cases.json"), "utf8")
);

const secretKeyPatterns = [
  "token", "secret", "password", "authorization",
  "api_key", "apikey", "cookie", "credential", "private_key"
];
const secretValuePatterns = [
  /(Bearer\s+)\S+/i,
  /\bsk-[a-zA-Z0-9]{20,}\b/i,
  /\bghp_[a-zA-Z0-9]{30,}\b/i,
  /\bgithub_pat_[a-zA-Z0-9]{22,}\b/i,
  /\bxox[baprs]-[a-zA-Z0-9-]+\b/i,
  /(api[_-]?key|apikey|token|password|secret|authorization)\s*[:=]\s*\S+/i
];

function redactString(value) {
  let s = value;
  for (const pat of secretValuePatterns) {
    s = s.replace(pat, (m, g1) => (g1 ? g1 + "<redacted>" : "<redacted>"));
  }
  return s;
}

function redactValue(value, depth = 0) {
  if (depth > 16) return "<max-depth>";
  if (value === null || value === undefined) return value;
  if (typeof value === "string") return redactString(value);
  if (Array.isArray(value)) return value.map((v) => redactValue(v, depth + 1));
  if (typeof value === "object") {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      const isSecret = secretKeyPatterns.some((p) => k.toLowerCase().includes(p));
      out[k] = isSecret ? "<redacted>" : redactValue(v, depth + 1);
    }
    return out;
  }
  return value;
}

describe("T4 preflight redaction", () => {
  for (const c of fixtures.cases) {
    it(`${c.name}: redacts as expected`, () => {
      const result = redactValue(c.input);
      if (c.expected !== undefined) {
        assert.deepStrictEqual(result, c.expected);
      }
      if (c.expected_contains) {
        assert.ok(JSON.stringify(result).includes(c.expected_contains), "expected redaction marker present");
      }
      if (c.expected_not_contains) {
        assert.ok(!JSON.stringify(result).includes(c.expected_not_contains), "secret substring removed");
      }
    });
  }
});
