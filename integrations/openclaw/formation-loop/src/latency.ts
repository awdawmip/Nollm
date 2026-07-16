import { appendFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname } from "node:path";

export const COMMIT_LATENCY_SCHEMA = "nollm_memory_commit_latency_v1";
export const RECALL_LATENCY_SCHEMA = "nollm_memory_recall_latency_v1";

export type LatencyClock = {
  epochMs(): number;
  monotonicNs(): bigint;
};

export const systemLatencyClock: LatencyClock = {
  epochMs: () => Date.now(),
  monotonicNs: () => process.hrtime.bigint(),
};

export function durationUs(startedNs: bigint, completedNs: bigint): number {
  if (completedNs < startedNs) throw new RangeError("monotonic clock moved backwards");
  return Number((completedNs - startedNs) / 1_000n);
}

export function durationMs(startedNs: bigint, completedNs: bigint): number {
  return durationUs(startedNs, completedNs) / 1_000;
}

export function sha256Text(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function turnCorrelationId(sessionKey: string, runId: string | undefined, visibleAnswer: string): string {
  return sha256Text(`${sessionKey}\0${runId ?? ""}\0${sha256Text(visibleAnswer)}`);
}

export type LatencyValidationConfig = {
  latency_validation_enabled?: boolean;
  latency_evidence_path?: string;
  latency_scenario_id?: string;
  latency_validation_run_id?: string;
};

export async function appendLatencyEvent(
  config: LatencyValidationConfig,
  schemaVersion: typeof COMMIT_LATENCY_SCHEMA | typeof RECALL_LATENCY_SCHEMA,
  event: Record<string, unknown>,
  clock: LatencyClock = systemLatencyClock,
): Promise<void> {
  if (!config.latency_validation_enabled || !config.latency_evidence_path) return;
  const record = {
    schema_version: schemaVersion,
    event_epoch_ms: clock.epochMs(),
    scenario_id: config.latency_scenario_id ?? "unspecified",
    validation_run_id: config.latency_validation_run_id ?? "unspecified",
    ...event,
  };
  await mkdir(dirname(config.latency_evidence_path), { recursive: true });
  await appendFile(config.latency_evidence_path, `${JSON.stringify(record)}\n`, "utf8");
}
