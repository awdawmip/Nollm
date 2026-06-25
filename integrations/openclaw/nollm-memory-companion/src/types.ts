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

export type PythonProbeResult = {
  executable: string;
  version: string;
  sysPrefix: string;
  platform: string;
};