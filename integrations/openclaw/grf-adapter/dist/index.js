import { Type } from "typebox";
import { spawn } from "node:child_process";
import { buildJsonPluginConfigSchema, definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
const toolNames = ["nollm_capture", "nollm_prepare_placement", "nollm_apply_placement", "nollm_recall", "nollm_show_source", "nollm_status"];
const placementActions = ["reuse", "new", "revision", "stitch", "defer"];
function deferred(reason) {
    return { content: [{ type: "text", text: JSON.stringify({ action: "defer", reason, placement_protocol: "nollm_grf_placement_v1" }) }], details: {} };
}
async function bridge(config, command, payload) {
    const python = config.python_executable;
    const repoRoot = config.nollm_repo_root;
    const storageRoot = config.nollm_storage_root;
    if (!python || !repoRoot || !storageRoot)
        return { ok: false, error: "explicit_host_bridge_not_configured" };
    const pythonPath = `${repoRoot}\\reference\\python`;
    const input = JSON.stringify({ command, payload, workspace: storageRoot });
    return await new Promise((resolve) => {
        const child = spawn(python, ["-c", "from nollm.grf.openclaw_bridge import main; main()"], { env: { ...process.env, PYTHONPATH: pythonPath }, windowsHide: true, stdio: "pipe" });
        let stdout = "";
        let stderr = "";
        const timer = setTimeout(() => { child.kill(); resolve({ ok: false, error: "bridge_timeout" }); }, 30_000);
        child.stdout.on("data", (chunk) => { stdout += chunk.toString("utf8"); });
        child.stderr.on("data", (chunk) => { stderr += chunk.toString("utf8"); });
        child.on("error", (error) => { clearTimeout(timer); resolve({ ok: false, error: error.message }); });
        child.on("close", () => { clearTimeout(timer); try {
            resolve(JSON.parse(stdout));
        }
        catch {
            resolve({ ok: false, error: stderr || "bridge_invalid_json" });
        } });
        child.stdin.end(input);
    });
}
function toolResult(value) {
    return { content: [{ type: "text", text: JSON.stringify(value) }], details: value };
}
function registerTools(api, config) {
    for (const name of toolNames) {
        api.registerTool({
            name,
            label: name,
            description: `Nollm GRF ${name.replace("nollm_", "").replaceAll("_", " ")}.`,
            parameters: Type.Object({ request: Type.Optional(Type.Unknown()) }),
            async execute(_id, params) {
                if (name === "nollm_status" && params.request === undefined)
                    return toolResult({ plugin: "nollm-grf", state: "loaded", placement_actions: placementActions });
                const command = name.replace("nollm_", "").replace("prepare_placement", "prepare_placement").replace("apply_placement", "apply_placement");
                const result = await bridge(config, command, params.request ?? {});
                return result.ok ? toolResult(result.result) : deferred(result.error ?? "bridge_failure");
            },
        });
    }
}
function registerHooks(api, config) {
    const observe = (hook) => () => api.logger.debug?.(`nollm-grf observed ${hook}`);
    api.on("message_received", observe("message_received"));
    api.on("agent_turn_prepare", () => undefined);
    api.on("before_prompt_build", () => undefined);
    api.on("agent_end", observe("agent_end"));
    api.on("after_tool_call", observe("after_tool_call"));
    api.on("message_sent", observe("message_sent"));
    api.on("session_start", observe("session_start"));
    api.on("session_end", observe("session_end"));
    api.on("before_compaction", observe("before_compaction"));
    api.on("after_compaction", observe("after_compaction"));
    api.on("gateway_start", observe("gateway_start"));
    api.on("gateway_stop", observe("gateway_stop"));
    api.logger.info(`nollm-grf loaded with placement_mode=${config.placement_mode ?? "assisted"}`);
}
const plugin = definePluginEntry({
    id: "nollm-grf",
    name: "Nollm GRF",
    description: "Geometry-native Nollm integration.",
    configSchema: buildJsonPluginConfigSchema({}),
    register(api) {
        const config = (api.pluginConfig ?? {});
        if (config.enabled === false)
            return;
        registerTools(api, config);
        registerHooks(api, config);
        api.registerCommand({ name: "nollm-grf-status", description: "Show Nollm GRF plugin status.", handler: () => ({ text: "nollm-grf loaded" }) });
    },
});
export default plugin;
