import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const providerRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(providerRoot, "..", "..", "..");
const expectedCommit = "dc9c11be917ebdc711b956250aa80a8e5b47bea6";
const upstreamUrl = "https://github.com/openclaw/openclaw.git";
const nodeBin = process.execPath;

// D6.2: Node runtime gate - verify Node satisfies OpenClaw engines requirement
const REQUIRED_NODE_MAJOR = 22;
const REQUIRED_NODE_MINOR = 19;
const currentNodeMajor = parseInt(process.versions.node.split(".")[0], 10);
const currentNodeMinor = parseInt(process.versions.node.split(".")[1], 10);
const nodeEngineOk = currentNodeMajor > REQUIRED_NODE_MAJOR ||
  (currentNodeMajor === REQUIRED_NODE_MAJOR && currentNodeMinor >= REQUIRED_NODE_MINOR);

function npmCommandArgs(args) {
  if (process.platform !== "win32") {
    return { cmd: "npm", args };
  }
  const candidates = [
    path.join(path.dirname(nodeBin), "node_modules", "npm", "bin", "npm-cli.js"),
    path.join(path.dirname(nodeBin), "..", "lib", "node_modules", "npm", "bin", "npm-cli.js"),
  ];
  for (const npmCliJs of candidates) {
    if (fs.existsSync(npmCliJs)) {
      return { cmd: nodeBin, args: [npmCliJs, ...args] };
    }
  }
  return { cmd: "npm.cmd", args };
}

function run(cmd, args, cwd, envExtras = {}, maxOutput = 4000) {
  return new Promise((resolve) => {
    const opts = { cwd, shell: false };
    const extraKeys = Object.keys(envExtras);
    if (extraKeys.length > 0) {
      opts.env = { ...process.env };
      for (const key of extraKeys) {
        if (key === "NODE_PATH") {
          const current = opts.env[key];
          const separator = process.platform === "win32" ? ";" : ":";
          opts.env[key] = current ? `${envExtras[key]}${separator}${current}` : envExtras[key];
        } else {
          opts.env[key] = envExtras[key];
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
      resolve({
        cmd, args, cwd,
        start,
        end: new Date().toISOString(),
        code: null,
        error: error.message,
        stdout: stdout.slice(0, maxOutput),
        stderr: stderr.slice(0, maxOutput),
      });
    });
    child.on("close", (code) => {
      resolve({
        cmd, args, cwd,
        start,
        end: new Date().toISOString(),
        code,
        stdout: stdout.slice(0, maxOutput),
        stderr: stderr.slice(0, maxOutput),
      });
    });
  });
}

function isGitRepo(dir) {
  return fs.existsSync(path.join(dir, ".git"));
}

async function provisionCheckout(envCheckout) {
  const steps = [];
  let checkout = envCheckout;

  // D2: verify or provision exact upstream checkout
  if (!checkout || !fs.existsSync(checkout) || !isGitRepo(checkout)) {
    checkout = path.join(os.tmpdir(), `openclaw-f0-04-${Date.now()}`);
    fs.mkdirSync(checkout, { recursive: true });
    steps.push({
      name: "provision_temp_checkout",
      ok: true,
      checkout,
      note: "NOLLM_OPENCLAW_CHECKOUT not set or invalid; provisioning temp checkout",
    });

    const clone = await run("git", ["clone", "--no-checkout", upstreamUrl, checkout], repoRoot);
    steps.push({ name: "git_clone", ...clone, ok: clone.code === 0 });
    if (clone.code !== 0) {
      return { checkout: null, steps, blocked: "git_clone_failed" };
    }

    const fetch = await run("git", ["fetch", "--depth", "1", "origin", expectedCommit], checkout);
    steps.push({ name: "git_fetch_commit", ...fetch, ok: fetch.code === 0 });
    if (fetch.code !== 0) {
      return { checkout: null, steps, blocked: "git_fetch_commit_failed" };
    }

    const checkoutCmd = await run("git", ["checkout", "-f", expectedCommit], checkout);
    steps.push({ name: "git_checkout_commit", ...checkoutCmd, ok: checkoutCmd.code === 0 });
    if (checkoutCmd.code !== 0) {
      return { checkout: null, steps, blocked: "git_checkout_commit_failed" };
    }
  }

  const head = await run("git", ["rev-parse", "HEAD"], checkout);
  const actualCommit = head.stdout.trim();
  steps.push({
    name: "verify_upstream_commit",
    ...head,
    ok: actualCommit === expectedCommit,
    actualCommit,
    expectedCommit,
  });
  if (actualCommit !== expectedCommit) {
    return { checkout: null, steps, blocked: "commit_mismatch" };
  }

  // D2: install dependencies if missing
  const nodeModulesPath = path.join(checkout, "node_modules");
  if (!fs.existsSync(nodeModulesPath)) {
    const installCmd = npmCommandArgs(["ci"]);
    const install = await run(installCmd.cmd, installCmd.args, checkout);
    steps.push({ name: "npm_ci", ...install, ok: install.code === 0 });
    if (install.code !== 0) {
      return { checkout: null, steps, blocked: "npm_ci_failed" };
    }
  } else {
    steps.push({ name: "npm_ci", ok: true, skipped: true, reason: "node_modules present" });
  }

  // D2: build if dist missing
  const distPath = path.join(checkout, "dist");
  if (!fs.existsSync(distPath)) {
    const buildCmd = npmCommandArgs(["run", "build"]);
    const build = await run(buildCmd.cmd, buildCmd.args, checkout);
    steps.push({ name: "openclaw_build", ...build, ok: build.code === 0 });
    if (build.code !== 0) {
      return { checkout: null, steps, blocked: "openclaw_build_failed" };
    }
  } else {
    steps.push({ name: "openclaw_build", ok: true, skipped: true, reason: "dist present" });
  }

  return { checkout, steps, blocked: null };
}

async function makeIsolatedOpenClawProfile() {
  const profileDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "oc-f0-04-profile-"));
  const openclawDir = path.join(profileDir, ".openclaw");
  await fs.promises.mkdir(openclawDir, { recursive: true });
  // D1: real isolated config selecting nollm as the memory slot
  const profile = {
    plugins: {
      enabled: true,
      slots: { memory: "nollm" },
      entries: {
        nollm: { enabled: true, config: {} },
        "memory-core": { enabled: false },
        "active-memory": { enabled: false },
      },
    },
  };
  await fs.promises.writeFile(path.join(openclawDir, "openclaw.json"), JSON.stringify(profile, null, 2), "utf8");
  return profileDir;
}

function profileEnv(profileDir) {
  return process.platform === "win32"
    ? { USERPROFILE: profileDir }
    : { HOME: profileDir };
}

async function main() {
  const results = {
    schema: "nollm.f0_04.integration_harness.v1",
    timestamp: new Date().toISOString(),
    repoRoot,
    providerRoot,
    expectedCommit,
    nodeEngineOk,
    nodeVersion: process.versions.node,
    steps: [],
    knownLimitations: [],
    blocked: null,
  };

  if (!nodeEngineOk) {
    results.blocked = `node_engine_unsatisfied: requires >=${REQUIRED_NODE_MAJOR}.${REQUIRED_NODE_MINOR}, got ${process.versions.node}`;
    console.error(JSON.stringify(results, null, 2));
    process.exit(1);
  }

  const envCheckout = process.env.NOLLM_OPENCLAW_CHECKOUT || "";
  const provision = await provisionCheckout(envCheckout);
  results.steps.push(...provision.steps);
  if (provision.blocked) {
    results.blocked = provision.blocked;
    console.error(JSON.stringify(results, null, 2));
    process.exit(1);
  }
  const tempCheckout = provision.checkout;

  const profileDir = await makeIsolatedOpenClawProfile();
  results.steps.push({
    name: "isolated_openclaw_profile",
    ok: true,
    profileDir,
  });

  // Build provider
  const providerBuildCmd = npmCommandArgs(["run", "build"]);
  const buildResult = await run(providerBuildCmd.cmd, providerBuildCmd.args, providerRoot, profileEnv(profileDir));
  results.steps.push({
    name: "provider_build",
    ok: buildResult.code === 0,
    ...buildResult,
  });
  if (buildResult.code !== 0) {
    console.error(JSON.stringify(results, null, 2));
    process.exit(1);
  }

  // D1: Real OpenClaw host integration via host-integration-check.mjs
  const dataRoot = path.join(os.tmpdir(), `nollm-f0-04-data-${Date.now()}`).replace(/\\/g, "/");
  fs.mkdirSync(dataRoot, { recursive: true });
  const fixturePath = path.resolve(providerRoot, "fixtures", "alpha-field.json").replace(/\\/g, "/");
  const hostCheckScript = path.resolve(providerRoot, "scripts", "host-integration-check.mjs");
  const hostLoadResult = await run(
    nodeBin,
    [hostCheckScript],
    providerRoot,
    {
      ...profileEnv(profileDir),
      NODE_PATH: path.join(tempCheckout, "node_modules"),
      NOLLM_OPENCLAW_CHECKOUT: tempCheckout,
      NOLLM_DATA_ROOT: dataRoot,
      PYTHON_EXE: process.env.PYTHON_EXE || "python3",
      NOLLM_REPO_ROOT: repoRoot.replace(/\\/g, "/"),
      NOLLM_FIXTURE_PATH: fixturePath,
    },
    1024 * 1024
  );

  let hostLoadOk = false;
  let hostChecks = {};
  let hostTargetLimitation = null;
  try {
    const parsed = JSON.parse(hostLoadResult.stdout);
    hostLoadOk = parsed.ok === true;
    hostChecks = parsed.checks || {};
    hostTargetLimitation = parsed.target_limitation || null;
  } catch {
    hostLoadOk = false;
  }

  results.steps.push({
    name: "host_integration_load",
    ok: hostLoadOk,
    target_limitation: hostTargetLimitation,
    ...hostLoadResult,
    checks: hostChecks,
  });

  if (hostTargetLimitation) {
    results.knownLimitations.push(hostTargetLimitation);
  }

  const outputDir = path.join(repoRoot, "out");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, "f0-04-integration-harness.json");
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), "utf8");

  console.log(JSON.stringify(results, null, 2));
  process.exit(hostLoadOk ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
