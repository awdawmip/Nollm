import { spawn } from "node:child_process";
import { Buffer } from "node:buffer";
import path from "node:path";
import { safeAgentSegment } from "./config.js";

const MAX_OUTPUT_BYTES = 1024 * 1024;

function appendBounded(current, chunk) {
  const next = current + chunk.toString("utf8");
  if (Buffer.byteLength(next, "utf8") <= MAX_OUTPUT_BYTES) return next;
  return next.slice(0, MAX_OUTPUT_BYTES);
}

function spawnJson(command, args, stdin, timeoutMs, env, signal) {
  return new Promise((resolve) => {
    if (signal?.aborted) {
      resolve({ ok: false, error: "bridge_aborted", retryable: true });
      return;
    }
    const child = spawn(command, args, { shell: false, windowsHide: true, stdio: ["pipe", "pipe", "pipe"], env });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      resolve(value);
    };
    const abort = () => {
      try { child.kill(process.platform === "win32" ? undefined : "SIGKILL"); } catch {}
      finish({ ok: false, error: "bridge_aborted", retryable: true });
    };
    const timer = setTimeout(() => {
      try { child.kill(process.platform === "win32" ? undefined : "SIGKILL"); } catch {}
      finish({ ok: false, error: "bridge_timeout", retryable: true });
    }, timeoutMs);
    signal?.addEventListener("abort", abort, { once: true });
    child.stdout.on("data", (chunk) => { stdout = appendBounded(stdout, chunk); });
    child.stderr.on("data", (chunk) => { stderr = appendBounded(stderr, chunk); });
    child.on("error", (error) => finish({ ok: false, error: "bridge_process_error", detail: String(error), retryable: true }));
    child.on("close", (code) => {
      if (settled) return;
      if (code !== 0) {
        finish({ ok: false, error: "bridge_process_error", detail: (stderr || stdout).slice(0, 4000), retryable: true });
        return;
      }
      try {
        finish(JSON.parse(stdout));
      } catch {
        finish({ ok: false, error: "bridge_invalid_json", detail: stderr.slice(0, 4000), retryable: true });
      }
    });
    child.stdin.end(stdin, "utf8");
  });
}

export class NollmBridgeRuntime {
  constructor(config) {
    this.config = config;
  }

  get available() {
    return this.config.runtimeMode !== "unavailable";
  }

  workspaceForAgent(agentId) {
    if (this.config.memoryWorkspace) return this.config.memoryWorkspace;
    return path.join(this.config.dataRoot, safeAgentSegment(agentId));
  }

  async call(envelope, signal) {
    if (!this.available) {
      return { ok: false, error: "runtime_unavailable", retryable: false };
    }
    const wire = JSON.stringify(envelope);
    const framed = Buffer.from(wire, "utf8").toString("base64");
    if (this.config.runtimeMode === "packaged") {
      return await spawnJson(
        this.config.runtimeExecutable,
        [...this.config.runtimeArgs, "bridge"],
        framed,
        this.config.commandTimeoutMs,
        { ...process.env, NOLLM_BRIDGE_BASE64: "1", PYTHONUTF8: "1" },
        signal
      );
    }
    const pythonPath = [
      path.join(this.config.nollmRepoRoot, "packages/nollm-core/src"),
      path.join(this.config.nollmRepoRoot, "packages/nollm-access/src"),
      path.join(this.config.nollmRepoRoot, "integrations/openclaw/formation-loop/python")
    ].join(path.delimiter);
    return await spawnJson(
      this.config.pythonExecutable,
      ["-m", "nollm_openclaw_formation.bridge"],
      framed,
      this.config.commandTimeoutMs,
      { ...process.env, NOLLM_BRIDGE_BASE64: "1", PYTHONUTF8: "1", PYTHONPATH: pythonPath },
      signal
    );
  }
}
