export type PluginConfig = {
  pythonCommand?: string;
  pythonExecutable?: string;
  pythonArgs?: string[];
  nollmRepoRoot?: string;
  workspaceRoot?: string;
  sidecarScript?: string;
  sidecarOutDir?: string;
  commandTimeoutMs?: number;
  maxSearchResults?: number;
};

export type NormalizedConfig = {
  pythonExecutable: string;
  pythonArgs: string[];
  nollmRepoRoot: string;
  workspaceRoot: string;
  sidecarScript: string;
  sidecarOutDir: string;
  commandTimeoutMs: number;
  maxSearchResults: number;
};

export type PythonProbeErrorCode =
  | "windows_python_executable_required"
  | "python_executable_not_found"
  | "python_executable_not_absolute"
  | "python_executable_probe_failed"
  | "legacy_python_launcher_rejected";

export type SidecarErrorCode =
  | "sidecar_timeout"
  | "sidecar_failed"
  | "sidecar_invalid_json"
  | "configuration_error"
  | "commit_rejected"
  | PythonProbeErrorCode;

export type NativeError = {
  ok: false;
  schema: string;
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
  [key: string]: unknown;
};

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
  schema: string;
  [key: string]: unknown;
};

export type SidecarResult = SidecarSuccess | NativeError | SidecarFailure;

export type PythonProbeResult = {
  executable: string;
  version: string;
  sysPrefix: string;
  platform: string;
};
