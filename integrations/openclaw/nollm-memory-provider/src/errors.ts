import type { SidecarFailure } from "./types.js";

export function sidecarFailure(
  code: SidecarFailure["error"]["code"],
  message: string,
  retryable: boolean
): SidecarFailure {
  return {
    ok: false,
    error: { code, message, retryable },
  };
}

export function safeErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message.slice(0, 240);
  }
  return "Nollm sidecar adapter error.";
}
