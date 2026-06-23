import type { OpenClawPluginDefinition } from "openclaw/plugin-sdk/plugin-entry";
import {
  buildJsonPluginConfigSchema,
  definePluginEntry,
} from "openclaw/plugin-sdk/plugin-entry";
import { ConfigSchema } from "./config.js";
import { createNollmProvider } from "./provider.js";

const plugin: OpenClawPluginDefinition = definePluginEntry({
  id: "nollm",
  name: "Nollm Memory",
  description: "Nollm native active memory provider for OpenClaw Functional Alpha.",
  kind: "memory",
  configSchema: buildJsonPluginConfigSchema(
    ConfigSchema as unknown as Parameters<typeof buildJsonPluginConfigSchema>[0]
  ),
  register(api) {
    createNollmProvider(api);
  },
});

export default plugin;
