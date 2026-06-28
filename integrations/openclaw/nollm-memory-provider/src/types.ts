export type PluginConfig = {
  pythonExecutable?: string;
  pythonArgs?: string[];
  nollmRepoRoot?: string;
  workspaceRoot?: string;
  nativeStoreRoot?: string;
  trialRoot?: string;
  commandTimeoutMs?: number;
  maxFacts?: number;
  maxContextCharacters?: number;
  captureMode?: string;
  trialMode?: string;
  trialId?: string;
};

export type NormalizedConfig = {
  pythonExecutable: string;
  pythonArgs: string[];
  nollmRepoRoot: string;
  workspaceRoot: string;
  nativeStoreRoot: string;
  trialRoot: string;
  sidecarScript: string;
  commandTimeoutMs: number;
  maxFacts: number;
  maxContextCharacters: number;
  captureMode: string;
  trialMode: string;
  trialId?: string;
};

export type SidecarErrorCode =
  | "sidecar_timeout"
  | "sidecar_failed"
  | "sidecar_invalid_json"
  | "configuration_error"
  | "field_unavailable"
  | "field_malformed"
  | "invalid_command"
  | "capture_failed";

export type SidecarFailure = {
  ok: false;
  error: {
    code: SidecarErrorCode;
    message: string;
    retryable: boolean;
  };
};

export type SidecarSuccess = {
  ok: true;
  [key: string]: unknown;
};

export type SidecarResult = SidecarSuccess | SidecarFailure;

export type MemoryFact = {
  memory_id: string;
  claim: string;
  kind: string;
  source: string;
  revision_id?: string;
};

export type MemoryContextEnvelope = {
  schema: "NOLLM_MEMORY_CONTEXT_V1";
  freshness: "fresh" | "none" | "unavailable";
  facts: MemoryFact[];
  boundaries: Array<Record<string, unknown>>;
  warnings: string[];
  explicit_absences: string[];
};

export type ActivePrepareResult = {
  schema: "nollm.provider.prepare.v2";
  ok: true;
  context: MemoryContextEnvelope;
  metrics?: {
    native_record_count?: number;
    result_count?: number;
    rendered_context_characters?: number;
    recall_mode?: string;
  };
};

export type ActiveCaptureResult = {
  schema: "nollm.active_memory_capture.v1";
  ok: true;
  capture: {
    event_id: string;
    promoted_count: number;
    deduplicated_count: number;
    suppressed_count: number;
    rejected_count: number;
    records: Array<{
      memory_id: string;
      kind: string;
      source: string;
    }>;
  };
  metrics?: {
    user_messages_seen?: number;
    assistant_messages_ignored?: number;
    candidate_count?: number;
    latency_ms?: number;
  };
};
