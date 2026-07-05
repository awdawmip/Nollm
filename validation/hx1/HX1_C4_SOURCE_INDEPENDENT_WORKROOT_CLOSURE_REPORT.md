# HX1-C4 Source-Independent Work-root Containment Closure Report

## Scope

HX1-C4 closes the C3 work-root containment gap where repository protection depended on the caller process cwd.

Delivered:

- Protected repository roots are discovered from the HX1 source module path and from the caller cwd.
- `.git` file or directory ancestors are recognized with pathlib-only checks.
- Source repository root and descendants are rejected even when the caller cwd is outside the repository.
- Caller-cwd repository root and descendants remain rejected when the caller starts inside another repository.
- Missing `.git` ancestors are ignored, so installed-package or temporary-directory execution does not reject every root.
- Explicit external owned temporary work-roots remain valid.
- Rejection happens before marker, receipt, Evidence, Capture, Cortex, Admission, Assembly, Recall, or DG6 stage writes.

Not delivered:

- OpenClaw, runtime, external API, daemon, network, database, cache, session, LLM/NLP, embeddings, semantic search, global discovery, automatic admission, automatic placement, subprocess/git-based root discovery, or sealed production module changes.

## Validation Targets

- External cwd plus source repository descendant is rejected with `HX1_WORK_ROOT_REJECTED`, creates no probe directory, and has empty `git status --short -- .hx1_c4_external_cwd_probe`.
- External cwd plus source repository root is rejected with `HX1_WORK_ROOT_REJECTED` before creating an HX1 marker.
- External cwd plus external temporary work-root completes the normal mixed A/B/C plus pre-existing D scenario.
- Existing C3 checks for repository root, repository descendant, invalid work-root type, and external roots are preserved.
- Normal HX1 report output remains byte-identical with SHA-256 `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`.

## Validation Results

- `python -m pytest -q reference/python/tests/test_hx1_trusted_host_bridge.py reference/python/tests/test_hx1_host_binding_preflight.py reference/python/tests/test_hx1_staged_outcomes.py reference/python/tests/test_hx1_receipt_regeneration.py reference/python/tests/test_hx1_boundaries.py`
  - Result: `60 passed in 7.78s`
- `python validation/hx1/run_hx1_validation.py --output validation/hx1/HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md`
  - Result: pass
  - SHA-256: `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`
- `git diff --exit-code -- validation/hx1/HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md docs/validation/HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md`
  - Result: pass
- CX2 / DG7 / DG6 / DG5 / DX2 preservation pytest group:
  - Result: `120 passed in 27.02s`
- Manual public API external-cwd evidence:
  - Source repository descendant work-root: rejected, no probe directory.
  - Source repository root work-root: rejected.
  - External temporary work-root: completed.
- Protected root discovery summary:
  - Source module repository is protected.
  - Current cwd repository is protected when cwd is inside the same repository.
  - Public errors do not expose machine absolute paths.
- Static forbidden import scan:
  - Result: pass for host execution imports.
- Source repository probe git status:
  - Result: no untracked probe output.
- Fresh-process normal report SHA-256:
  - Run 1: `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`
  - Run 2: `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`
- `python run_tests.py`
  - Result: timed out after 904 seconds without a completed result.
- `python -m nollm.cli validate ../../examples/openclaw`
  - Result: `PASS`
- `python -m nollm.cli audit ../../examples/openclaw`
  - Result: pass, `issue_count = 0`.

## Changed Boundaries

- Production code changes are limited to `reference/python/nollm/dream_geometry/host_execution`.
- Tests are limited to `reference/python/tests/test_hx1_*.py`.
- Documentation changes are limited to HX1 protocol, integration, delivery, validation, and roadmap files.
- Sealed implementation modules outside HX1 host execution were not modified.
