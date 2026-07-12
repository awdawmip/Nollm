# AOLD OpenClaw Natural Chat Live Truth Report

Date: 2026-07-12

## Result

OpenClaw 2026.6.11 on Windows loaded plugin 0.2.0 and exposed `nollm_form_statement` to the main agent through stable tool policy. Fifteen frozen normal-chat cases produced 16 autonomous plugin calls and 16 real internal LLM calls. Three ordinary controls did not trigger the tool. Direct tool RPC, chat commands, raw tool envelopes, case-specific prompt injection, accepted rewritten text, accepted invalid spans, and Python semantic fallback were all zero.

The plugin uses Python `build_prompt` and `parse_result` as the single canonical prompt/schema path. Prompt version is `aold-v3`; schema version is `aold-formation-v1`. Windows `.cmd` resolution launches sibling `node.exe` and `node_modules/openclaw/openclaw.mjs`; configured Python is the real `sys.executable`, not a batch wrapper. At most one parser-feedback retry is permitted; the frozen evidence includes a successful two-attempt case.

## Lifecycle

Install, enable, Gateway load, runtime inspection, tool registration, disable, re-enable, reload, and uninstall were executed. Similar ordinary chat produced zero plugin calls while disabled and after uninstall. Calls resumed after re-enable and after a separate Gateway reload. Final host state is uninstalled.

## Reviews

The prior 36 corpus reviews are now classified as assistant reviews: 33 accept, 3 partial, 0 reject. Human reviewed case count is 0. No assistant review is reported as human review.

## Progress

Expected and actual vector: ACCESS 0%, OPENCLAW +10%, LAB +5%, DISTRIBUTIONS +5%; all other modules 0%. ACCESS remains 65%, OPENCLAW advances from 30% to 40%, LAB from 65% to 70%, and DISTRIBUTIONS from 50% to 55%. V3.1 remains the stable modular baseline and V3.2 is the current OpenClaw-first semantic route.

## Limits

This is a bounded Windows natural-chat capability validation, not broad semantic quality or product release. It does not validate Placement, Recall, persistence, real memory integration, broad user data, or cross-platform operation. Existing OpenClaw legacy state-migration warnings remained unrelated.
