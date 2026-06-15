# Nollm Dream Geometry Failure Triage

Status: OK

## Summary

- Reports checked: 5
- Missing reports: 0
- Failed reports: 0
- Forbidden semantics detected: false

## Components

| Component | Present | OK | Notes |
| --- | --- | --- | --- |
| all_dream_checks_manifest | true | true | required_reports: 2 |
| dream_suite | true | true | components: 3 |
| golden_regression | true | true | failed_report_count: 0 |
| local_gate | true | true | pytest included: false |
| real_corpus_dry_run | true | true | shard_count: 8 |

## Forbidden Semantics

| Flag | Detected |
| --- | --- |
| parent_child | false |
| anchor_ownership | false |
| folder_tree | false |
| confirmed_placement | false |

## Warnings

- E9 is an internal triage report.
- E9 is not a stable V1 recall/tool surface.
