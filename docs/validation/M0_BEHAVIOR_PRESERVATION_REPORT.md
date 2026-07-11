# M0 Behavior Preservation Report

Date: 2026-07-11

## Scope

M0 established ownership and package boundaries without modifying existing GRF,
Dream Geometry, OpenClaw adapter, Snapshot, Recall, or Host production
implementation. The only moved assets were the OpenClaw development corpus and
paused result files; every move was Git identity-preserving (`R100`).

No existing test was deleted. No live OpenClaw update, LLM corpus run, PB/1M
benchmark, remote GitHub operation, or repository split was started.

## Before and After

| Check | Before M0 move | After M0 move | Result |
| --- | ---: | ---: | --- |
| GRF suite (`reference/python/tests/grf`) | 112 passed | 112 passed | Preserved |
| Existing Snapshot/Trace selection | Not separately recorded | 111 passed | Passed |
| M0 Snapshot/Trace ports and imports | Not present | 7 passed | Passed |
| Repository/package hygiene | Existing contract | 8 passed | Passed after README compatibility terms were restored |
| Module boundary checker | Not present | 642 reviewed baseline, 0 new; 1 reviewed cycle | Passed |
| `git diff --check` | Not applicable | Passed | Clean |

The pre-move GRF run completed in 7.30 seconds. The post-move GRF run completed
in 6.37 seconds. Both used `PYTHONDONTWRITEBYTECODE=1`,
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, and the repository's public Python path.

## Contract Coverage

- Public package imports: all six Python package roots import successfully.
- Snapshot: consistent-read begin/export/end, failure cleanup, restore, clone,
  verify, and policy-free structural comparison are covered.
- Trace: NullTrace result equivalence, canonical JSONL, metrics, memory capture,
  event stability classes, and composite sink failure isolation are covered.
- Recall and current Host fixtures: covered by the unchanged GRF suite,
  including host registry, capture/import, and recall tests.
- Boundary firewall: all tracked Python and TypeScript/JavaScript sources are
  scanned from the ownership manifest. New package violations are zero.

## Existing Debt

The baseline records 642 imports from the pre-M0 mixed architecture that violate
the target ownership graph and one cycle across Access, Core, Snapshot, and
Trace. Each finding carries its manifest migration action and is assigned to M1
extraction or removal. M0 does not hide or semantically rewrite this debt.

The external relation index is explicitly `BLOCKED / DELETE_LATER`; Python
semantic placement remains `BLOCKED / SPLIT`. LOW-confidence assets remain
preserved or quarantined and were not deleted.
