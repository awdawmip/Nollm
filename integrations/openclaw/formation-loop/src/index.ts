import { Type } from "typebox";
import { spawn } from "node:child_process";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";

function run(command: string, args: string[], input?: string, timeoutMs = 120000): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const child = spawn(command, args, { windowsHide: true, stdio: "pipe" });
    let stdout = ""; let stderr = ""; let settled = false;
    const finish = (value: { code: number; stdout: string; stderr: string }) => { if (!settled) { settled = true; clearTimeout(timer); resolve(value); } };
    const timer = setTimeout(() => { child.kill(); finish({ code: -1, stdout, stderr: "timeout" }); }, timeoutMs);
    child.stdout.on("data", chunk => { stdout += chunk.toString("utf8"); });
    child.stderr.on("data", chunk => { stderr += chunk.toString("utf8"); });
    child.on("error", error => finish({ code: -1, stdout, stderr: error.message }));
    child.on("close", code => finish({ code: code ?? -1, stdout, stderr }));
    child.stdin.end(input);
  });
}

const ConfigSchema = Type.Object({
  python_executable: Type.Optional(Type.String()), nollm_repo_root: Type.Optional(Type.String()),
  openclaw_command: Type.Optional(Type.String()), model: Type.Optional(Type.String()),
  timeout_ms: Type.Optional(Type.Integer({ minimum: 1000, default: 120000 })),
}, { additionalProperties: false });

const plugin = defineToolPlugin({
  id: "nollm-formation",
  name: "Nollm Statement Formation",
  description: "Exact-span Statement Formation through a real OpenClaw model and the public Nollm Access contract.",
  configSchema: ConfigSchema,
  tools: (tool) => [
    tool({
      name: "nollm_form_statement",
      label: "Nollm form statement",
      description: "Select exact source spans as memory statements, or defer. Does not place or persist statements.",
      parameters: Type.Object({ request: Type.Unknown() }),
      async execute(params, config, context) {
        if (!config.python_executable || !config.nollm_repo_root || !config.openclaw_command || !config.model) return { ok: false, error: "explicit_configuration_required" };
        const prompt = `Return raw JSON only. Select continuous exact source spans or defer. Never rewrite. Schema: formed {"schema_version":"aold-formation-v1","outcome":"formed","selections":[{"evidence_id":"...","start":0,"end":1,"statement_id":"..."}],"reason_summary":"..."}; defer has empty selections plus reason_class and reason_summary. Input: ${JSON.stringify(params.request)}`;
        const inference = await run(config.openclaw_command, ["infer", "model", "run", "--json", "--model", config.model, "--prompt", prompt], undefined, config.timeout_ms ?? 120000);
        if (inference.code !== 0) return { ok: false, error: "llm_call_error", detail: inference.stderr };
        let raw: string;
        try { raw = JSON.parse(inference.stdout).outputs[0].text; } catch { return { ok: false, error: "llm_envelope_error" }; }
        const pythonPath = `${config.nollm_repo_root}\\packages\\nollm-core\\src;${config.nollm_repo_root}\\packages\\nollm-access\\src;${config.nollm_repo_root}\\integrations\\openclaw\\formation-loop\\python`;
        const input = JSON.stringify({ request: params.request, openclaw_command: config.openclaw_command, model: config.model, raw_model_response: raw, decision_id: `openclaw-${context.toolCallId}` });
        const bridge = await new Promise<{ code: number; stdout: string; stderr: string }>((resolve) => {
          const child = spawn(config.python_executable!, ["-m", "nollm_openclaw_formation.bridge"], { windowsHide: true, stdio: "pipe", env: { ...process.env, PYTHONPATH: pythonPath } });
          let stdout = ""; let stderr = "";
          child.stdout.on("data", chunk => { stdout += chunk.toString("utf8"); }); child.stderr.on("data", chunk => { stderr += chunk.toString("utf8"); });
          child.on("close", code => resolve({ code: code ?? -1, stdout, stderr })); child.stdin.end(input);
        });
        try { return JSON.parse(bridge.stdout); } catch { return { ok: false, error: "bridge_invalid_json", detail: bridge.stderr }; }
      },
    }),
  ],
});

export default plugin;
