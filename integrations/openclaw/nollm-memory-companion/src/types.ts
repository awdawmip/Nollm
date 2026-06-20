export type PluginConfig = {
  pythonCommand?: string;
  nollmRepoRoot?: string;
  workspaceRoot?: string;
  sidecarScript?: string;
  sidecarOutDir?: string;
  commandTimeoutMs?: number;
  maxSearchResults?: number;
};

export type NormalizedConfig = {
  pythonCommand: string;
  nollmRepoRoot: string;
  workspaceRoot: string;
  sidecarScript: string;
  sidecarOutDir: string;
  commandTimeoutMs: number;
  maxSearchResults: number;
};

export type SidecarErrorCode =
  | "sidecar_timeout"
  | "sidecar_failed"
  | "sidecar_invalid_json"
  | "configuration_error"
  | "commit_rejected";

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
