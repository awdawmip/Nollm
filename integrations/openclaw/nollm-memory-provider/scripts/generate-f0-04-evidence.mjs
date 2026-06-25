import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const providerRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(providerRoot, "..", "..", "..");
const outDir = path.join(repoRoot, "out");
fs.mkdirSync(outDir, { recursive: true });

function run(cmd, args, cwd, envExtras = {}) {
  return new Promise((resolve) => {
    const opts = { cwd, shell: false };
    if (Object.keys(envExtras).length > 0) {
      opts.env = { ...process.env };
      for (const [k, v] of Object.entries(envExtras)) {
        if (k === "NODE_PATH") {
          const sep = process.platform === "win32" ? ";" : ":";
          opts.env[k] = opts.env[k] ? `${v}${sep}${opts.env[k]}` : v;
        } else {
          opts.env[k] = v;
        }
      }
    }
    const start = new Date().toISOString();
    const child = spawn(cmd, args, opts);
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (d) => { stdout += d; });
    child.stderr.on("data", (d) => { stderr += d; });
    child.on("error", (error) => {
      resolve({ cmd, args, cwd, start, end: new Date().toISOString(), code: null, error: error.message, stdout, stderr });
    });
    child.on("close", (code) => {
      resolve({ cmd, args, cwd, start, end: new Date().toISOString(), code, stdout, stderr });
    });
  });
}

function sha256(text) {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

function bounded(text, max = 4000) {
  if (text.length <= max) return text;
  return text.slice(0, max) + "\n... [truncated for excerpt; full output SHA-256 above] ...";
}

function parseNodeTestCounts(text) {
  const m = text.match(/ℹ tests (\d+)[\s\S]*?ℹ pass (\d+)[\s\S]*?ℹ fail (\d+)[\s\S]*?ℹ skipped (\d+)/);
  if (!m) return null;
  return { framework: "node-test", total: parseInt(m[1], 10), pass: parseInt(m[2], 10), fail: parseInt(m[3], 10), skip: parseInt(m[4], 10) };
}

function parsePytestCounts(text) {
  const m = text.match(/(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?/);
  if (!m) return null;
  const pass = parseInt(m[1], 10);
  const fail = m[2] ? parseInt(m[2], 10) : 0;
  const skip = m[3] ? parseInt(m[3], 10) : 0;
  return { framework: "pytest", total: pass + fail + skip, pass, fail, skip };
}

async function gitHash(file) {
  const r = await run("git", ["hash-object", file], repoRoot);
  return r.stdout.trim();
}

async function main() {
  const evidence = {
    schema: "nollm.f0_04.evidence.v1",
    generatedAt: new Date().toISOString(),
    generator: "integrations/openclaw/nollm-memory-provider/scripts/generate-f0-04-evidence.mjs",
    environment: {
      node: process.versions.node,
      npm: null,
      python: null,
      platform: process.platform,
      arch: process.arch,
      cwd: process.cwd(),
    },
    repo: { root: repoRoot, branch: null, head: null, statusLines: [] },
    artifacts: [],
    commands: [],
    knownLimitations: [],
    remote: {},
  };

  const npmV = await run("npm", ["-v"], repoRoot);
  evidence.environment.npm = npmV.stdout.trim();
  const pyV = await run("python", ["--version"], repoRoot);
  evidence.environment.python = pyV.stdout.trim() || pyV.stderr.trim();

  const branchR = await run("git", ["branch", "--show-current"], repoRoot);
  evidence.repo.branch = branchR.stdout.trim();
  const headR = await run("git", ["rev-parse", "HEAD"], repoRoot);
  evidence.repo.head = headR.stdout.trim();
  const statusR = await run("git", ["status", "--short"], repoRoot);
  evidence.repo.statusLines = statusR.stdout.trim().split("\n").filter(Boolean);

  const artifactPaths = [
    "integrations/openclaw/nollm-memory-provider/package.json",
    "integrations/openclaw/nollm-memory-provider/openclaw.plugin.json",
    "integrations/openclaw/nollm-memory-provider/src/provider.ts",
    "integrations/openclaw/nollm-memory-provider/src/identity.ts",
    "integrations/openclaw/nollm-memory-provider/src/config.ts",
    "integrations/openclaw/nollm-memory-provider/src/compat-registry.ts",
    "integrations/openclaw/nollm-memory-provider/src/memory-runtime.ts",
    "integrations/openclaw/nollm-memory-provider/scripts/host-integration-check.mjs",
    "integrations/openclaw/nollm-memory-provider/scripts/integration-harness.mjs",
    "integrations/openclaw/nollm-memory-provider/scripts/generate-f0-04-evidence.mjs",
    "reference/python/nollm/openclaw_memory_provider_alpha.py",
    "reference/python/tests/test_openclaw_memory_provider_alpha.py",
    "docs/integration/openclaw/issues/FA-ISSUE-10-loader-local-memory-plugin.md",
  ];
  for (const rel of artifactPaths) {
    const full = path.join(repoRoot, rel);
    if (!fs.existsSync(full)) continue;
    evidence.artifacts.push({ path: rel, sha256: await gitHash(full) });
  }

  const tsR = await run("npm", ["test"], providerRoot);
  evidence.commands.push({
    name: "ts_provider_tests",
    argv: ["npm", "test"],
    cwd: providerRoot,
    start: tsR.start,
    end: tsR.end,
    exitCode: tsR.code,
    stdoutSha256: sha256(tsR.stdout),
    stderrSha256: sha256(tsR.stderr),
    stdoutExcerpt: bounded(tsR.stdout),
    stderrExcerpt: bounded(tsR.stderr),
    parsedCounts: parseNodeTestCounts(tsR.stdout),
  });

  const pyRoot = path.join(repoRoot, "reference/python");
  const pyR = await run("python", ["-m", "pytest", "tests/test_openclaw_memory_provider_alpha.py", "tests/test_openclaw_memory_adapter_docs.py", "tests/test_native_field.py", "-v"], pyRoot);
  evidence.commands.push({
    name: "python_provider_tests",
    argv: ["python", "-m", "pytest", "tests/test_openclaw_memory_provider_alpha.py", "tests/test_openclaw_memory_adapter_docs.py", "tests/test_native_field.py", "-v"],
    cwd: pyRoot,
    start: pyR.start,
    end: pyR.end,
    exitCode: pyR.code,
    stdoutSha256: sha256(pyR.stdout),
    stderrSha256: sha256(pyR.stderr),
    stdoutExcerpt: bounded(pyR.stdout),
    stderrExcerpt: bounded(pyR.stderr),
    parsedCounts: parsePytestCounts(pyR.stdout),
  });

  const envCheckout = process.env.NOLLM_OPENCLAW_CHECKOUT || "";
  const evidenceBranch = process.env.NOLLM_F0_04_EVIDENCE_BRANCH || "evidence/f0-04-openclaw-memory-provider-unspecified";
  if (!envCheckout) {
    evidence.commands.push({ name: "integration_harness", skipped: true, reason: "NOLLM_OPENCLAW_CHECKOUT not set" });
  } else {
    const harnessR = await run("node", ["scripts/integration-harness.mjs"], providerRoot, { NOLLM_OPENCLAW_CHECKOUT: envCheckout });
    let harnessJson = null;
    try { harnessJson = JSON.parse(harnessR.stdout); } catch {}
    evidence.commands.push({
      name: "integration_harness",
      argv: ["node", "scripts/integration-harness.mjs"],
      cwd: providerRoot,
      envSummary: { NOLLM_OPENCLAW_CHECKOUT: envCheckout },
      start: harnessR.start,
      end: harnessR.end,
      exitCode: harnessR.code,
      stdoutSha256: sha256(harnessR.stdout),
      stderrSha256: sha256(harnessR.stderr),
      stdoutExcerpt: bounded(harnessR.stdout),
      stderrExcerpt: bounded(harnessR.stderr),
      parsedHarness: harnessJson ? {
        nodeEngineOk: harnessJson.nodeEngineOk,
        expectedCommit: harnessJson.expectedCommit,
        blocked: harnessJson.blocked,
        knownLimitations: harnessJson.knownLimitations,
      } : null,
    });
    if (harnessJson?.knownLimitations?.length) {
      evidence.knownLimitations.push(...harnessJson.knownLimitations);
    }
  }

  const remoteUrl = await run("git", ["remote", "get-url", "origin"], repoRoot);
  evidence.remote.originUrl = { ok: remoteUrl.code === 0, output: (remoteUrl.stdout + remoteUrl.stderr).trim() };
  const pushProject = await run("git", ["push", "-u", "origin", evidence.repo.branch], repoRoot);
  evidence.remote.pushProjectBranch = { ok: pushProject.code === 0, output: (pushProject.stdout + pushProject.stderr).trim() };
  const pushEvidence = await run("git", ["push", "-u", "origin", evidenceBranch], repoRoot);
  evidence.remote.pushEvidenceBranch = { ok: pushEvidence.code === 0, output: (pushEvidence.stdout + pushEvidence.stderr).trim() };
  const lsProject = await run("git", ["ls-remote", "--heads", "origin", evidence.repo.branch], repoRoot);
  evidence.remote.lsProjectBranch = { ok: lsProject.code === 0, output: (lsProject.stdout + lsProject.stderr).trim() };
  const lsEvidence = await run("git", ["ls-remote", "--heads", "origin", evidenceBranch], repoRoot);
  evidence.remote.lsEvidenceBranch = { ok: lsEvidence.code === 0, output: (lsEvidence.stdout + lsEvidence.stderr).trim() };

  const evidencePath = path.join(outDir, "f0-04-evidence.json");
  fs.writeFileSync(evidencePath, JSON.stringify(evidence, null, 2), "utf8");

  const md = makeCommandsAndResultsMd(evidence);
  fs.writeFileSync(path.join(outDir, "commands_and_results.md"), md, "utf8");

  console.log(JSON.stringify({ ok: true, evidencePath, commands: evidence.commands.map(c => ({ name: c.name, exitCode: c.exitCode, parsedCounts: c.parsedCounts, parsedHarness: c.parsedHarness })) }, null, 2));
}

function makeCommandsAndResultsMd(ev) {
  const lines = [];
  lines.push("# F0-04 Commands and Results");
  lines.push("");
  lines.push(`Generated: ${ev.generatedAt}`);
  lines.push(`Branch: ${ev.repo.branch}`);
  lines.push(`HEAD: ${ev.repo.head}`);
  lines.push(`Node: ${ev.environment.node} | npm: ${ev.environment.npm} | Python: ${ev.environment.python}`);
  lines.push("");
  lines.push("## Artifact hashes");
  lines.push("");
  for (const a of ev.artifacts) {
    lines.push(`- ${a.path}: \`${a.sha256}\``);
  }
  lines.push("");
  lines.push("## Command records");
  lines.push("");
  for (const c of ev.commands) {
    lines.push(`### ${c.name}`);
    if (c.skipped) {
      lines.push(`Skipped: ${c.reason}`);
      lines.push("");
      continue;
    }
    lines.push(`- argv: \`${c.argv.join(" ")}\``);
    lines.push(`- cwd: ${c.cwd}`);
    lines.push(`- exit code: ${c.exitCode}`);
    lines.push(`- start: ${c.start}`);
    lines.push(`- end: ${c.end}`);
    if (c.envSummary) lines.push(`- env summary: ${JSON.stringify(c.envSummary)}`);
    lines.push(`- stdout SHA-256: ${c.stdoutSha256}`);
    lines.push(`- stderr SHA-256: ${c.stderrSha256}`);
    if (c.parsedCounts) lines.push(`- parsed counts: ${JSON.stringify(c.parsedCounts)}`);
    if (c.parsedHarness) lines.push(`- parsed harness: ${JSON.stringify(c.parsedHarness)}`);
    lines.push("");
    lines.push("**stdout excerpt:**");
    lines.push("```");
    lines.push(c.stdoutExcerpt);
    lines.push("```");
    if (c.stderrExcerpt) {
      lines.push("");
      lines.push("**stderr excerpt:**");
      lines.push("```");
      lines.push(c.stderrExcerpt);
      lines.push("```");
    }
    lines.push("");
  }
  lines.push("## Remote status");
  lines.push("");
  for (const [k, v] of Object.entries(ev.remote)) {
    lines.push(`- ${k}: ok=${v.ok}, output=${v.output}`);
  }
  lines.push("");
  if (ev.knownLimitations.length) {
    lines.push("## Known limitations");
    lines.push("");
    for (const lim of ev.knownLimitations) {
      lines.push(`- ${lim.code}: ${lim.message}`);
    }
    lines.push("");
  }
  return lines.join("\n");
}

main().catch((err) => { console.error(err); process.exit(1); });
