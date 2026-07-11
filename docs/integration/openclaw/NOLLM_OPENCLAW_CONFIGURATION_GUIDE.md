# Configuration Guide

Defaults are `placement_mode=assisted`, `placement_execution=isolated-llm-task`, and `invalid_decision_policy=defer`. Configure explicit repository, storage, and Python paths under `plugins.entries.nollm-grf.config`.

For conversation hooks set `plugins.entries.nollm-grf.hooks.allowConversationAccess=true`. Add `llm-task` to the active agent's `tools.alsoAllow`, not only a global tools path.
