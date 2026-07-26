import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import process from "node:process";

const repo = path.resolve(process.argv[2] ?? ".");
const require = createRequire(path.join(repo, "integrations/openclaw/formation-loop/package.json"));
const ts = require("typescript");
const sourcePath = path.join(repo, "integrations/openclaw/formation-loop/src/index.ts");
const sourceText = fs.readFileSync(sourcePath, "utf8");
const source = ts.createSourceFile(sourcePath, sourceText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
const functions = new Map();
const callbacks = [];

function walk(node, visit) {
  visit(node);
  ts.forEachChild(node, child => walk(child, visit));
}

walk(source, node => {
  if (ts.isFunctionDeclaration(node) && node.name) functions.set(node.name.text, node);
  if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer &&
      (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer))) {
    functions.set(node.name.text, node.initializer);
  }
  if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) &&
      ts.isIdentifier(node.expression.expression) && node.expression.expression.text === "api") {
    if (node.expression.name.text === "on" && node.arguments[1]) callbacks.push(node.arguments[1]);
    if (node.expression.name.text === "registerService" && node.arguments[0] && ts.isObjectLiteralExpression(node.arguments[0])) {
      for (const member of node.arguments[0].properties) {
        if (ts.isMethodDeclaration(member) || ts.isPropertyAssignment(member)) callbacks.push(member);
      }
    }
    if (node.expression.name.text === "registerTool" && node.arguments[0] && ts.isObjectLiteralExpression(node.arguments[0])) {
      for (const member of node.arguments[0].properties) {
        if ((ts.isMethodDeclaration(member) || ts.isPropertyAssignment(member)) && member.name?.getText(source) === "execute") callbacks.push(member);
      }
    }
  }
});

if (functions.has("absorbCapturedBatch")) callbacks.push(functions.get("absorbCapturedBatch"));

const reachableFunctions = new Set();
const reachableNodes = [];
const activeActions = new Set();
const queue = [...callbacks];
while (queue.length) {
  const root = queue.shift();
  if (!root || reachableNodes.includes(root)) continue;
  reachableNodes.push(root);
  function visit(node) {
    if (node !== root && (ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node) || ts.isArrowFunction(node) || ts.isMethodDeclaration(node))) return;
    if (ts.isCallExpression(node)) {
      if (ts.isIdentifier(node.expression)) {
        const name = node.expression.text;
        if (functions.has(name) && !reachableFunctions.has(name)) {
          reachableFunctions.add(name);
          queue.push(functions.get(name));
        }
        if (name === "bridge" && node.arguments[1] && ts.isObjectLiteralExpression(node.arguments[1])) {
          const action = node.arguments[1].properties.find(item => item.name?.getText(source) === "action");
          if (action && ts.isPropertyAssignment(action) && ts.isStringLiteral(action.initializer)) activeActions.add(action.initializer.text);
        }
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(root);
}

const legacyActions = new Set([
  "build_dream_prompt", "parse_dream_result", "build_dream_format_repair_prompt",
  "build_dream_sculptor_prompt", "parse_dream_sculptor_result", "apply_dream_sculptor_result",
  "build_prompt", "parse_result",
]);
const reachableLegacyActions = [...activeActions].filter(item => legacyActions.has(item)).sort();
const reachableText = reachableNodes.map(node => node.getText(source)).join("\n");
const categoryTerms = /sensitive|secret|password|credential|medical|weather|temporary|tool noise|no_memory|question defer/i;
let contentCategoryBranches = 0;
let sourceRoleAdmissionGates = 0;
for (const root of reachableNodes) {
  walk(root, node => {
    let condition;
    if (ts.isIfStatement(node) || ts.isConditionalExpression(node) || ts.isWhileStatement(node) || ts.isDoStatement(node)) condition = node.expression;
    if (!condition) return;
    const text = condition.getText(source);
    if (categoryTerms.test(text)) contentCategoryBranches += 1;
    if (/role/i.test(text) && /(defer|reject|eligible|admit|no_memory)/i.test(node.getText(source))) sourceRoleAdmissionGates += 1;
  });
}

const pythonRoot = path.join(repo, "integrations/openclaw/formation-loop/python/nollm_openclaw_formation");
const pythonGate = path.join(repo, "lab/nollm-lab/recall_lens/run_v311r61_python_import_gate.py");
const { spawnSync } = await import("node:child_process");
const python = process.env.NOLLM_TEST_PYTHON ?? "python";
const pythonRun = spawnSync(python, [pythonGate, pythonRoot], { encoding: "utf8" });
if (pythonRun.status !== 0) throw new Error(`Python import gate failed: ${pythonRun.stderr || pythonRun.stdout}`);
const pythonResult = JSON.parse(pythonRun.stdout);

const manifest = JSON.parse(fs.readFileSync(path.join(repo, "integrations/openclaw/formation-loop/openclaw.plugin.json"), "utf8"));
const diagnose = fs.readFileSync(path.join(repo, "integrations/openclaw/formation-loop/scripts/diagnose.ps1"), "utf8");
const diagnoseStates = ["evaluated_no_new_propositions", "structural_invalid", "admitted", "reused", "revised", "retryable_defer", "incomplete_continuation"];
const result = {
  schema_version: "nollm_v311r61_active_pipeline_gate_v1",
  active_semantic_entrypoints: ["register hooks", "nollm_memory.execute", "absorbCapturedBatch"],
  active_prompts: [...activeActions].filter(item => item.startsWith("build_")).sort(),
  active_actions: [...activeActions].sort(),
  reachable_function_count: reachableFunctions.size,
  legacy_reachable_count: reachableLegacyActions.length + pythonResult.legacy_reachable_count,
  reachable_legacy_actions: reachableLegacyActions,
  reachable_legacy_python_modules: pythonResult.reachable_legacy_modules,
  content_category_branch_count: contentCategoryBranches + pythonResult.content_category_branch_count,
  source_role_gate_count: sourceRoleAdmissionGates + pythonResult.source_role_gate_count,
  tool_exact_evidence_support: manifest.contracts?.toolEvidenceWire === "nollm_openclaw_tool_evidence_v1" &&
    reachableText.includes("publishToolEvidence") && reachableText.includes("toolEvidenceIds"),
  diagnose_status_set: diagnoseStates.filter(item => diagnose.includes(item)),
  legacy_formation_public_api: manifest.contracts?.legacyFormationPublicApi,
};
const pass = result.legacy_reachable_count === 0 && result.content_category_branch_count === 0 &&
  result.source_role_gate_count === 0 && result.tool_exact_evidence_support === true &&
  result.diagnose_status_set.length === diagnoseStates.length && result.legacy_formation_public_api === "none";
console.log(JSON.stringify({ ...result, status: pass ? "PASS" : "FAIL" }));
process.exitCode = pass ? 0 : 1;
