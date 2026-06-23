export type PluginConfig = {
  pythonCommand?: string;
  nollmRepoRoot?: string;
  nollmDataRoot?: string;
  alphaFixturePath?: string;
  commandTimeoutMs?: number;
  maxFacts?: number;
  maxCharacters?: number;
  captureMode?: string;
};

export type NormalizedConfig = {
  pythonCommand: string;
  nollmRepoRoot: string;
  nollmDataRoot: string;
  alphaFixturePath: string;
  sidecarScript: string;
  commandTimeoutMs: number;
  maxFacts: number;
  maxCharacters: number;
  captureMode: string;
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

export type MemoryContextEnvelope = {
  schema: "nollm.memory_context.v1";
  context_id: string;
  field_id: string;
  field_revision_id: string;
  freshness: "fresh" | "none" | "unavailable";
  facts: Array<Record<string, unknown>>;
  boundaries: Array<Record<string, unknown>>;
  warnings: string[];
  completeness: {
    mode: "bounded";
    explicit_absences: string[];
  };
};

export type CaptureReceipt = {
  receipt_id: string;
  event_hash: string;
  stored_at: string;
  state: "captured_pending_native_ingress";
  legacy_memory_mutated: false;
};
