import type { OpenClawPluginDefinition } from "openclaw/plugin-sdk/plugin-entry";
import {
  buildJsonPluginConfigSchema,
  definePluginEntry,
} from "openclaw/plugin-sdk/plugin-entry";
import { ConfigSchema } from "./config.js";

// HISTORICAL_INVALID_FOR_CONTENT_ADMISSION: retained only as audit evidence.

const plugin: OpenClawPluginDefinition = definePluginEntry({
  id: "nollm",
  name: "Nollm Memory",
  description: "HISTORICAL_INVALID_FOR_CONTENT_ADMISSION; quarantined and fail-closed.",
  kind: "memory",
  configSchema: buildJsonPluginConfigSchema(
    ConfigSchema as unknown as Parameters<typeof buildJsonPluginConfigSchema>[0]
  ),
  register(api) {
    void api;
    throw new Error("HISTORICAL_INVALID_FOR_CONTENT_ADMISSION");
  },
});

export default plugin;
