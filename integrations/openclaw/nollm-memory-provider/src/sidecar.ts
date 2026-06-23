import { spawn } from "node:child_process";
import { safeErrorMessage, sidecarFailure } from "./errors.js";
import type { NormalizedConfig, SidecarResult } from "./types.js";

const MAX_CAPTURE_BYTES = 256 * 1024;

export async function runSidecarCommand(
  config: NormalizedConfig,
  command: "prepare" | "capture" | "status",
  payload: Record<string, unknown>,
  signal?: AbortSignal
): Promise<SidecarResult> {
  const configJson = JSON.stringify({
    pythonCommand: config.pythonCommand,
    nollmRepoRoot: config.nollmRepoRoot,
    nollmDataRoot: config.nollmDataRoot,
    alphaFixturePath: config.alphaFixturePath,
    commandTimeoutMs: config.commandTimeoutMs,
    maxFacts: config.maxFacts,
    maxCharacters: config.maxCharacters,
    captureMode: config.captureMode,
  });
  const stdinPayload = JSON.stringify({ command, ...payload });
  return spawnJson(
    config.pythonCommand,
    [config.sidecarScript, "--config-json", configJson],
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
      if (code !== 0) {
        finish(
          sidecarFailure(
            "sidecar_failed",
            conciseSidecarFailure(stderr || stdout),
            true
          )
        );
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
  const firstLine =
    text.split(/\r?\n/).find((line) => line.trim()) ?? "Nollm sidecar command failed.";
  return firstLine.slice(0, 240);
}
