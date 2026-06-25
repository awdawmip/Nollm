import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { makeTempDir, listFiles, resolvePythonCommand } from "./helpers.mjs";
import { runSidecarCommand } from "../dist/sidecar.js";
import { normalizeConfig } from "../dist/config.js";

const REPO_ROOT = path.resolve(import.meta.dirname, "..", "..", "..", "..");
const PYTHON_SRC_FILES = [
  path.join(REPO_ROOT, "reference", "python", "nollm", "openclaw_memory_provider_alpha.py"),
  path.join(REPO_ROOT, "reference", "python", "scripts", "run_openclaw_nollm_provider.py"),
];

const FORBIDDEN_TS = [
  "MEMORY.md",
  "DREAMS.md",
  "memory_search",
  "memory_get",
  "memory_store",
  "memory_recall",
  "parse_openclaw_memory_workspace",
  "build_sidecar_store",
  "search_sidecar",
  "get_sidecar_item",
  "recall_sidecar",
];

const FORBIDDEN_PY = [
  "MEMORY.md",
  "DREAMS.md",
  "memory_search",
  "memory_get",
  "memory_store",
  "memory_recall",
  "parse_openclaw_memory_workspace",
  "build_sidecar_store",
  "search_sidecar",
  "get_sidecar_item",
  "recall_sidecar",
];

function isLegacyDetectionContext(text, token) {
  if (token !== "memory/" && token !== "\\memory\\") return false;
  const idx = text.indexOf("LEGACY_PATH_FRAGMENTS");
  if (idx === -1) return false;
  const block = text.slice(idx, idx + 400);
  return block.includes("memory/") || block.includes("\\memory\\");
}

function stripLeadingDocstring(text) {
  const trimmed = text.trimStart();
  if (!trimmed.startsWith('"""')) return text;
  const end = trimmed.indexOf('"""', 3);
  if (end === -1) return text;
  return trimmed.slice(end + 3);
}

describe("T12 static no-legacy-source scan passes", () => {
  it("TypeScript provider source does not reference legacy surfaces", () => {
    const srcDir = path.resolve(import.meta.dirname, "..", "src");
    const files = listFiles(srcDir, ".ts");
    for (const file of files) {
      const text = fs.readFileSync(file, "utf8");
      for (const token of FORBIDDEN_TS) {
        assert.ok(
          !text.includes(token),
          `${path.basename(file)} contains forbidden legacy reference: ${token}`
        );
      }
    }
  });

  it("Python alpha module does not reference legacy surfaces except detection constant", () => {
    for (const file of PYTHON_SRC_FILES) {
      assert.ok(fs.existsSync(file), `Python source missing: ${file}`);
      const text = fs.readFileSync(file, "utf8");
      const scanText = stripLeadingDocstring(text);
      for (const token of FORBIDDEN_PY) {
        if (scanText.includes(token)) {
          if (isLegacyDetectionContext(scanText, token)) continue;
          assert.fail(`${path.basename(file)} contains forbidden legacy reference: ${token}`);
        }
      }
    }
  });
});

describe("dynamic no-legacy access", () => {
  it("prepare and capture do not read or write legacy files", async () => {
    const tmp = makeTempDir();
    const dataRoot = path.join(tmp, "data");
    fs.mkdirSync(dataRoot, { recursive: true });

    const legacyDir = path.join(tmp, "legacy");
    fs.mkdirSync(path.join(legacyDir, "memory"), { recursive: true });
    fs.writeFileSync(
      path.join(legacyDir, "MEMORY.md"),
      "LEGACY_SENTINEL_DO_NOT_READ",
      "utf8"
    );
    fs.writeFileSync(
      path.join(legacyDir, "DREAMS.md"),
      "LEGACY_SENTINEL_DO_NOT_READ",
      "utf8"
    );
    fs.writeFileSync(
      path.join(legacyDir, "memory", "2026-06-23.md"),
      "LEGACY_SENTINEL_DO_NOT_READ",
      "utf8"
    );

    const cfg = {
      pythonCommand: resolvePythonCommand(),
      nollmRepoRoot: REPO_ROOT,
      nollmDataRoot: dataRoot,
      alphaFixturePath: path.join(
        REPO_ROOT,
        "integrations",
        "openclaw",
        "nollm-memory-provider",
        "fixtures",
        "alpha-field.json"
      ),
    };
    const normalized = normalizeConfig(cfg);

    const prepareResult = await runSidecarCommand(normalized, "prepare", {
      schema: "nollm.provider.prepare.v1",
      agent_id: "main",
      session_id: "s1",
      run_id: "run1",
      messages: [{ role: "user", content: "blue labels" }],
      budget: { max_facts: 3, max_characters: 1200 },
    });
    if (prepareResult.ok !== true) {
      console.error("prepare failed:", JSON.stringify(prepareResult, null, 2));
    }
    assert.equal(prepareResult.ok, true);
    assert.ok(
      !JSON.stringify(prepareResult).includes("LEGACY_SENTINEL"),
      "prepare output must not leak legacy sentinel"
    );

    const captureResult = await runSidecarCommand(normalized, "capture", {
      schema: "nollm.provider.capture.v2",
      agent_id: "main",
      session_id: "s1",
      run_id: "run1",
      success: true,
      messages: [{ role: "user", content: "blue" }],
    });
    if (captureResult.ok !== true) {
      console.error("capture failed:", JSON.stringify(captureResult, null, 2));
    }
    assert.equal(captureResult.ok, true);
    const storedPath = captureResult.receipt.stored_at;
    assert.ok(storedPath.includes("functional-alpha"));
    assert.ok(storedPath.startsWith(dataRoot));

    assert.equal(
      fs.readFileSync(path.join(legacyDir, "MEMORY.md"), "utf8"),
      "LEGACY_SENTINEL_DO_NOT_READ"
    );
    assert.equal(
      fs.readFileSync(path.join(legacyDir, "DREAMS.md"), "utf8"),
      "LEGACY_SENTINEL_DO_NOT_READ"
    );
    assert.equal(
      fs.readFileSync(path.join(legacyDir, "memory", "2026-06-23.md"), "utf8"),
      "LEGACY_SENTINEL_DO_NOT_READ"
    );
  });
});
