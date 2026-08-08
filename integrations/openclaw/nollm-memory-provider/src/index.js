import { buildJsonPluginConfigSchema, definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { ConfigSchema } from "./config.js";
import { createNollmProvider } from "./provider.js";

export default definePluginEntry({
  id: "nollm-memory",
  name: "Nollm Memory",
  description: "Geometry-native long-term memory slot for OpenClaw.",
  kind: "memory",
  configSchema: buildJsonPluginConfigSchema(ConfigSchema),
  register(api) {
    createNollmProvider(api);
  }
});
