# Independent native field deployment

Implementation date: 2026-11-25. Development base:
`e345b9a96b1495ce34807401080ef429e35c6e7c`.

An explicit deployment can now carry the native runtime, a settled field and
fixed original source files to another directory or repository. The receiving
Host starts with stored Surface, selects one physical entrance and follows actual
coverage. Source files are opened only through selected fixed references; their
inventory does not select an entrance or place semantic content.

The [deployment guide](../../lab/nollm-lab/repository_memory/PORTABLE_DEPLOYMENT.md)
documents `build_deployment.py` and the resulting `run.py`. The launcher supplies
its own field and snapshot, so ordinary encounters and original-source reads
work outside the Nollm checkout without Git or network access for materialized
sources. The snapshot adapter checks the existing Git blob identity and line
window at the evidence-read boundary. It reports missing or changed originals
explicitly. The builder records partial local materialization truthfully.

The installed runtime also carries the explicit Lab local-p8 evaluator. It
retains its own contract and does not change the field's Core Q40/96 geometry.
Installing a runtime and exporting a working field remain separate operations.
This facility does not install an account skill or change another knowledge
system's normal entry.

## Conditional-write recovery correction

`AccessRuntime.apply_if_state` previously deleted a newly captured Statement on
an ordinary exception even if placement and rollback had both failed. The Core
could still reference that Statement while its original evidence was gone.

The conditional attempt now begins at `pre_commit`; cleanup is limited to a
known pre-commit failure or completed rollback. An unknown commit retains the
original Statement and pending recovery record. Reopening Access uses the
existing recovery mechanism to restore placement and bindings. Existing evidence
is preserved, including after a previous successful attempt.

## Executed focused validation

| Scope | Distinct tests passed |
|---|---:|
| Access reorganization, including three new conditional-failure regressions | 15 |
| Content budget, local reorganization and physical storage/placement | 24 |
| Portable source and relocated deployment | 5 |
| Existing skill installer | 4 |
| Total | 48 |

The unknown-commit regression was observed failing before the fix and passing
after it. The portable integration test launches Python with `-I`, relocates the
deployment, moves the original field and sources away, and runs from an unrelated
working directory. It selects a native entrance, revises the encountered
judgment, reads the old original, reopens the current judgment and runs local-p8
with 96 total hits while checking that the field remains unchanged.

Other focused cases cover fixed-source line numbering and UTF-8/CRLF bytes,
wrong commits, altered originals, missing files, invalid citations before field
creation, partial snapshots and destination preservation. These are functional
and recovery checks; real-content formation and independent Host recall are
separate deployment evaluations. Historical full-suite counts are not added to
this run.

Run the relevant existing stdlib unittest files from the repository root with
`PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src:lab/nollm-lab/repository_memory`:

- `packages/nollm-access/tests/test_reorganization.py`
- `packages/nollm-access/tests/test_content_budget.py`
- `lab/nollm-lab/repository_memory/test_local_reorganization_review.py`
- `lab/nollm-lab/repository_memory/test_project_storage_and_placement.py`
- `lab/nollm-lab/repository_memory/test_portable_deployment.py`
- `lab/nollm-lab/repository_memory/test_skill_install.py`
