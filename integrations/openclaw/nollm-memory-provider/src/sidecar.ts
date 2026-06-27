import { spawn } from "node:child_process";
import { safeErrorMessage, sidecarFailure } from "./errors.js";
import type { NormalizedConfig, SidecarResult } from "./types.js";

const MAX_CAPTURE_BYTES = 256 * 1024;

export type ActiveCommand = "active-status" | "active-prepare" | "active-capture" | "active-trial-report";

export async function runSidecarCommand(
  config: NormalizedConfig,
  command: ActiveCommand,
  payload: Record<string, unknown>,
  signal?: AbortSignal
): Promise<SidecarResult> {
  const argv: string[] = [
    ...config.pythonArgs,
    config.sidecarScript,
    "--native-store-root",
    config.nativeStoreRoot,
    "--trial-root",
    config.trialRoot,
  ];
  const stdinPayload = JSON.stringify({ command, ...payload });
  return spawnJson(
    config.pythonExecutable,
    argv,
    stdinPayload,
    config.commandTimeoutMs,
    signal
  );
}

async function spawnJson(
  command: string,
  argv: string[],
  stdinPayload: string,
  timeoutMs: number,
  signal?: AbortSignal
): Promise<SidecarResult> {
  return new Promise((resolve) => {
    if (signal?.aborted) {
      resolve(
        sidecarFailure(
          "sidecar_timeout",
          "Nollm sidecar command was aborted before start.",
          true
        )
      );
      return;
    }

    const child = spawn(command, argv, {
      shell: false,
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let finished = false;

    const finish = (result: SidecarResult) => {
      if (finished) return;
      finished = true;
      resolve(result);
    };

    const timer = setTimeout(() => {
      timedOut = true;
      terminateChild(child);
    }, timeoutMs);

    const abort = () => {
      timedOut = true;
      terminateChild(child);
    };
    signal?.addEventListener("abort", abort, { once: true });

    child.stdout.on("data", (chunk: Buffer) => {
      stdout = appendBounded(stdout, chunk);
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr = appendBounded(stderr, chunk);
    });

    child.on("error", (error) => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      finish(sidecarFailure("sidecar_failed", safeErrorMessage(error), true));
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      if (timedOut) {
        finish(
          sidecarFailure("sidecar_timeout", "Nollm sidecar command timed out.", true)
        );
        return;
      }
      const parsed = parseAcceptedSidecarJson(stdout, stdinPayload);
      if (parsed) {
        finish(parsed);
        return;
      }
      if (code !== 0) {
        finish(sidecarFailure("sidecar_failed", conciseSidecarFailure(stderr || stdout), true));
        return;
      }
      try {
        finish(JSON.parse(stdout));
      } catch {
        finish(
          sidecarFailure(
            "sidecar_invalid_json",
            "Nollm sidecar returned invalid JSON.",
            true
          )
        );
      }
    });

    child.stdin.write(stdinPayload, "utf8", (err) => {
      if (err) {
        finish(sidecarFailure("sidecar_failed", safeErrorMessage(err), true));
        return;
      }
      child.stdin.end();
    });
  });
}

function terminateChild(child: ReturnType<typeof spawn>): void {
  try {
    if (process.platform === "win32") {
      child.kill();
    } else {
      child.kill("SIGKILL");
    }
  } catch {
    // Ignore failures when the process has already exited.
  }
}

function appendBounded(current: string, chunk: Buffer): string {
  const next = current + chunk.toString("utf8");
  if (Buffer.byteLength(next, "utf8") <= MAX_CAPTURE_BYTES) {
    return next;
  }
  return next.slice(0, MAX_CAPTURE_BYTES);
}

function conciseSidecarFailure(text: string): string {
  const allLines = text.split(/\r?\n/).filter((line) => line.trim());
  const lines =
    allLines.length <= 14
      ? allLines
      : [...allLines.slice(0, 6), "...", ...allLines.slice(-8)];
  const summary = lines.length > 0 ? lines.join(" | ") : "Nollm sidecar command failed.";
  return summary.slice(0, 3000);
}

function parseAcceptedSidecarJson(stdout: string, stdinPayload: string): SidecarResult | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(stdout);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== "object") {
    return null;
  }
  const obj = parsed as Record<string, unknown>;
  const schema = typeof obj.schema === "string" ? obj.schema : "";
  const invoked = invokedCommand(stdinPayload);
  const accepted = acceptedSchemas(invoked);
  if (!accepted.has(schema)) {
    return null;
  }
  if (obj.ok === false && schema === "nollm.active_memory_error.v1") {
    return parsed as SidecarResult;
  }
  if (obj.ok === true) {
    return parsed as SidecarResult;
  }
  return null;
}

function invokedCommand(stdinPayload: string): ActiveCommand | "" {
  try {
    const payload = JSON.parse(stdinPayload) as Record<string, unknown>;
    const command = payload.command;
    if (
      command === "active-status" ||
      command === "active-prepare" ||
      command === "active-capture" ||
      command === "active-trial-report"
    ) {
      return command;
    }
  } catch {
    // Ignore invalid input; the sidecar will report the command error.
  }
  return "";
}

function acceptedSchemas(command: ActiveCommand | ""): Set<string> {
  switch (command) {
    case "active-status":
      return new Set(["nollm.active_memory_status.v1", "nollm.active_memory_error.v1"]);
    case "active-prepare":
      return new Set(["nollm.provider.prepare.v2", "nollm.active_memory_error.v1"]);
    case "active-capture":
      return new Set(["nollm.active_memory_capture.v1", "nollm.active_memory_error.v1"]);
    case "active-trial-report":
      return new Set(["nollm.active_memory_trial_report.v1", "nollm.active_memory_error.v1"]);
    default:
      return new Set(["nollm.active_memory_error.v1"]);
  }
}
