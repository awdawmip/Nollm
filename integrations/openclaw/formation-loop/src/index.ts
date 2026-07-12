import { Type } from "typebox";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, extname, join } from "node:path";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";

export type RunResult = { code: number; stdout: string; stderr: string };
export type Launcher = { command: string; prefix: string[]; backend: "windows-node-launcher" | "direct-executable" };

export function resolveOpenClawLauncher(command: string, exists = existsSync): Launcher {
  if (extname(command).toLowerCase() !== ".cmd") return { command, prefix: [], backend: "direct-executable" };
  const root = dirname(command);
  const node = join(root, "node.exe");
  const module = join(root, "node_modules", "openclaw", "openclaw.mjs");
  if (!exists(node)) throw new Error("OpenClaw Node launcher is missing node.exe");
  if (!exists(module)) throw new Error("OpenClaw Node launcher is missing openclaw.mjs");
  return { command: node, prefix: ["--stack-size=8192", module], backend: "windows-node-launcher" };
}

export function run(command: string, args: string[], input?: string, timeoutMs = 120000, env?: NodeJS.ProcessEnv): Promise<RunResult> {
  return new Promise((resolve) => {
    const child = spawn(command, args, { windowsHide: true, stdio: "pipe", env });
    let stdout = ""; let stderr = ""; let settled = false;
    const finish = (value: RunResult) => { if (!settled) { settled = true; clearTimeout(timer); resolve(value); } };
    const timer = setTimeout(() => { child.kill(); finish({ code: -1, stdout, stderr: "timeout" }); }, timeoutMs);
    child.stdout.on("data", chunk => { stdout += chunk.toString("utf8"); });
    child.stderr.on("data", chunk => { stderr += chunk.toString("utf8"); });
    child.on("error", error => finish({ code: -1, stdout, stderr: error.message }));
    child.on("close", code => finish({ code: code ?? -1, stdout, stderr }));
    child.stdin.end(input);
  });
}

export function parseInferenceEnvelope(stdout: string): string {
  let value: unknown;
  try { value = JSON.parse(stdout); } catch { throw new Error("invalid OpenClaw JSON envelope"); }
  const text = (value as { outputs?: Array<{ text?: unknown }> }).outputs?.[0]?.text;
  if (typeof text !== "string" || !text.trim()) throw new Error("empty OpenClaw model output");
  return text.trim();
}

const ConfigSchema = Type.Object({
  python_executable: Type.Optional(Type.String()), nollm_repo_root: Type.Optional(Type.String()),
  openclaw_command: Type.Optional(Type.String()), model: Type.Optional(Type.String()),
  prompt_version: Type.Optional(Type.String({ default: "aold-v3" })),
  schema_version: Type.Optional(Type.String({ default: "aold-formation-v1" })),
  timeout_ms: Type.Optional(Type.Integer({ minimum: 1000, default: 120000 })),
}, { additionalProperties: false });

const Evidence = Type.Object({
  evidence_id: Type.String(), content_utf8: Type.String(), source_handle: Type.String(),
  context_refs: Type.Array(Type.String()),
}, { additionalProperties: false });
const FormationRequest = Type.Object({
  request_id: Type.String(), evidence: Type.Array(Evidence, { minItems: 1 }),
  max_statements: Type.Integer({ minimum: 1 }),
}, { additionalProperties: false });

type ToolConfig = { python_executable?: string; nollm_repo_root?: string; openclaw_command?: string; model?: string; prompt_version?: string; schema_version?: string; timeout_ms?: number };

function pythonPath(config: ToolConfig): string {
  return ["packages/nollm-core/src", "packages/nollm-access/src", "integrations/openclaw/formation-loop/python"]
    .map(path => join(config.nollm_repo_root!, path)).join(";");
}

async function bridge(config: ToolConfig, envelope: object): Promise<Record<string, unknown>> {
  const result = await run(config.python_executable!, ["-m", "nollm_openclaw_formation.bridge"], JSON.stringify(envelope), config.timeout_ms, { ...process.env, PYTHONPATH: pythonPath(config) });
  if (result.code !== 0) return { ok: false, error: "bridge_process_error", detail: result.stderr };
  try { return JSON.parse(result.stdout); } catch { return { ok: false, error: "bridge_invalid_json", detail: result.stderr }; }
}

const plugin = defineToolPlugin({
  id: "nollm-formation", name: "Nollm Statement Formation",
  description: "Exact-span Statement Formation through a real OpenClaw model and the public Nollm Access contract.",
  configSchema: ConfigSchema,
  tools: (tool) => [tool({
    name: "nollm_form_statement", label: "Nollm form statement",
    description: "Use for ordinary conversation that asks to remember durable facts or presents durable work facts worth forming. Supply the user's exact text as evidence; never summarize it. This only forms exact-span statements and may defer; it does not place or persist them.",
    parameters: Type.Object({ request: FormationRequest }, { additionalProperties: false }),
    async execute(params, config: ToolConfig, context) {
      if (!config.python_executable || !config.nollm_repo_root || !config.openclaw_command || !config.model) return { ok: false, error: "explicit_configuration_required" };
      const common = { request: params.request, openclaw_command: config.openclaw_command, model: config.model, prompt_version: config.prompt_version ?? "aold-v3", schema_version: config.schema_version ?? "aold-formation-v1" };
      let launcher: Launcher;
      try { launcher = resolveOpenClawLauncher(config.openclaw_command); } catch (error) { return { ok: false, error: "runtime_not_found", detail: String(error) }; }
      let retryError: string | undefined;
      for (let attempt = 0; attempt < 2; attempt += 1) {
        const built = await bridge(config, { action: "build_prompt", ...common, retry_error: retryError });
        if (built.ok !== true || typeof built.prompt !== "string") return built;
        const inference = await run(launcher.command, [...launcher.prefix, "infer", "model", "run", "--json", "--model", config.model, "--prompt", built.prompt], undefined, config.timeout_ms);
        if (inference.code !== 0) return { ok: false, error: inference.stderr === "timeout" ? "llm_timeout" : "llm_call_error", detail: inference.stderr, launcher_backend: launcher.backend };
        let raw: string;
        try { raw = parseInferenceEnvelope(inference.stdout); } catch (error) { retryError = String(error); if (attempt === 0) continue; return { ok: false, error: "llm_envelope_error", detail: retryError }; }
        const parsed = await bridge(config, { action: "parse_result", ...common, raw_model_response: raw, decision_id: `openclaw-${context.toolCallId}` });
        if (parsed.ok === true) return { ...parsed, runtime: { tool_call_id: context.toolCallId, attempt_count: attempt + 1, launcher_backend: launcher.backend, prompt_version: built.prompt_version, schema_version: built.schema_version, prompt_sha256: built.prompt_sha256, schema_sha256: built.schema_sha256, raw_model_response: raw, python_semantic_fallback: false } };
        retryError = `${String(parsed.error)}: ${String(parsed.message)}`;
        if (attempt === 1) return { ...parsed, runtime: { tool_call_id: context.toolCallId, attempt_count: 2, launcher_backend: launcher.backend, prompt_version: built.prompt_version, schema_version: built.schema_version, prompt_sha256: built.prompt_sha256, schema_sha256: built.schema_sha256, raw_model_response: raw, python_semantic_fallback: false } };
      }
      return { ok: false, error: "unreachable" };
    },
  })],
});

export default plugin;
