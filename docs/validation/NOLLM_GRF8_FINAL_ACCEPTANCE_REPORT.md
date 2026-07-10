# GRF8 Final Acceptance

## Scope And Environment

GRF8 was validated on Windows with PowerShell, Python for Windows, and Git for
Windows. All data, Host, and workflow inputs in this stage are deterministic
local fixtures. This is not a claim of a live production deployment, external
dataset generalization, or Linux/macOS portability.

## Gate Results

| Gate | Evidence | Result |
| --- | --- | --- |
| 0 | `run_grf7r4_snapshot_replay_validation.py`: independent temporary restore, identity samples, replay predicates, and negative controls | pass |
| A | `run_grf8_real_ingestion_validation.py`: six connector types, 10 shards, idempotent reload, retained source fallback | pass |
| B | `run_grf8_admission_validation.py`: capture/place/admit, manual/rule/batch paths, replacement fallback, incremental equals rebuild | pass |
| C | `run_grf8_global_field_validation.py`: bounded directory/source lookup, replay, bridge rollback, split/merge, incremental rebuild | pass |
| D | fixed-seed 10,000 EvidenceShard / 1,000-query fixture with six categories, revision chains, hard negatives, and eight query types | pass |
| E | eleven independently ranked baselines/ablations, real ranking metrics, N3/N4/N5 stitch and revision differences | pass |
| F | 600 coding/research/document/conversation queries under N5, source fallback and latest revision correctness both 1.0 | pass |
| G | File, Codex fixture, and OpenClaw fixture complete contract lifecycles plus restart/replay | pass |
| H | 1,000,000 mixed Windows operations, zero collision/orphan/replay/fallback failure | pass |
| I | three before/after measurements with positive improvement and no correctness difference | pass |
| J | public facade, shared host contract, Windows examples, required architecture/ingestion/host/quality/performance/limitations documents | pass |

## Quality And Workflow Limits

The N5 deterministic fixture reached Recall@5/MRR/nDCG@5/revision correctness
of 1.0 and missed-stitch rate 0.0. It also recorded a false-relation rate of
0.002. The research workflow recorded a false-relation rate of 0.01. Both are
retained in the benchmark output and are not excluded from the reported data.

N4 eliminates fixture stitch misses but resolves ordinary revisions only at
0.25 correctness; N5 is therefore required for the workflow result. These
measurements establish behavior only for this documented synthetic fixture.

## Long-Run Result

The final 1,000,000-operation run reported 408.52 operations/second,
Windows `GetProcessMemoryInfo` sampling, current RSS 773,103,616 bytes, peak
RSS 824,725,504 bytes, disk 481,312,315 bytes, and two maintenance partitions.
It performed capture, place, admit, recall, replay, revision, retire, move,
stitch, rollback, split/merge, and Host restart operations. Identity
collisions, orphans, replay failures, and fallback failures were all zero.

## Final Verification

The final code validation is:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python;$PWD"

python -m pytest -q reference/python/tests/grf
python -m pytest -q reference/python/tests/test_no_forbidden_features.py reference/python/tests/test_architecture_language.py reference/python/tests/test_repository_hygiene.py
python experiments/grf/run_grf7r4_snapshot_replay_validation.py
python experiments/grf/run_grf8_real_ingestion_validation.py
python experiments/grf/run_grf8_admission_validation.py
python experiments/grf/run_grf8_global_field_validation.py
python experiments/grf/run_grf8_memory_quality_benchmark.py
python experiments/grf/run_grf8_workflow_validation.py
python experiments/grf/run_grf8_host_integration.py
python experiments/grf/run_grf8_long_running_validation.py
python experiments/grf/run_grf8_performance_validation.py
```

The final clean commit was bundle-verified as complete history. This report
therefore issues `GRF8_ACCEPTED_CANDIDATE` for the documented Windows fixture
scope and limitations above.
