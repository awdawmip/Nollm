# AOLD OpenClaw Formation Live Loop Report

Date: 2026-07-12

Runtime was OpenClaw 2026.6.11 using local `infer model run` with `meituan/LongCat-2.0`. The retained validation contains 36 reviewed cases and 43 live calls: round 1 used 13 calls, round 2 used 14, round 3 used 13, and the retained negative E2E used 3. An earlier three-call negative diagnostic that missed the intended rejection categories is reported as an exploratory run and is not included in retained metrics.

## Iteration

- v1: strict raw JSON and exact code-point spans. Review found two under-splitting cases.
- v2: instructed the model to keep independently meaningful statements separate and consider each Evidence record. No Python splitter was added.
- v3: added model-side offset recount before submission and attempt-level failure records.
- Access contract change: none. Existing public exact-span validation was sufficient.

## Metrics

| Metric | Result |
| --- | ---: |
| live calls | 43 |
| parse success / valid exact span | 90.0% of three-round attempts |
| formed / defer | 83.33% / 16.67% of reviewed cases |
| retry rate | 11.11% of cases |
| human accept / partial / reject | 91.67% / 8.33% / 0% |
| source/context inheritance | 100% of accepted formed statements |
| median / p95 case latency | 48,921 / 116,019 ms |
| invalid span accepted | 0 |
| rewritten text accepted | 0 |
| Python semantic fallback | 0 |

All 36 final decisions were valid. Human review labeled 33 accept and 3 partial. Partial cases were exact and safe but under-split independent content. The negative E2E captured a real `end=999` response rejected as `invalid_span`, a real paraphrase field rejected as `rewritten_or_extra_text`, and a subsequent real-model retry accepted with an exact span.

## Operations

Official plugin validation passed. Actual link install, diagnose, parser smoke, disable, enable, and uninstall passed. Diagnose reported one tool, `nollm_form_statement`. The host was returned to an uninstalled state. Existing OpenClaw state-migration warnings about update-check/config-health SQLite divergence are unrelated and remain.

## Limits

This establishes a small real-model Formation capability record, not final semantic quality. It does not validate Placement, Recall, persistence, broad user data, formal release, automatic updates, or cross-platform behavior.
