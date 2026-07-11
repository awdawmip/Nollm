# OpenClaw Runtime Discovery Report

## Live Windows facts

- OpenClaw: `2026.6.11`.
- Gateway: scheduled Windows task, LAN bind on port `18789`.
- Plugin SDK entry: `openclaw/plugin-sdk` and `openclaw/plugin-sdk/plugin-entry`.
- Native plugin `nollm-grf` is loaded from `integrations/openclaw/grf-adapter/dist/index.js`.
- Bundled `llm-task` is enabled and loaded.
- Live smoke used provider/model `meituan/LongCat-2.0`.

## Verified public API

`api.on`, `api.registerTool`, `api.registerCommand`, and `api.logger` are public SDK surfaces. Runtime inspection confirms the twelve registered typed hooks, including `agent_end` after `hooks.allowConversationAccess=true`.

## Limits

Gateway restart can take several minutes before RPC is ready. The resumable corpus runner treats this as recoverable execution state, not a model-quality result.
