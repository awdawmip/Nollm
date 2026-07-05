# HX1-C3 Canonical Nested Preflight / Exact DG6 / Work-root Closure Report

## Scope

HX1-C3 closes canonicalization and reopen identity gaps in the trusted host bridge before fingerprinting, work-root creation, or staged execution.

Delivered:

- AdmissionPlacementPlan canonical preflight through sealed DA1 `placement_plan_payload` and fingerprint.
- DreamShard canonical preflight through sealed DE1 canonical payload and payload key.
- CompiledQueryProbe canonical preflight through sealed DC1 canonical payload and fingerprint.
- Complete canonical DreamShard payload binding in `execution_input_fingerprint`.
- Reopen mismatch when a same-plan same-root call changes DreamShard content or origin.
- DG6 declaration and binding are bidirectionally exact.
- Repository root and repository descendant work roots are rejected before writes.
- `work_root` type errors are classified as `HX1_INVALID_CONTEXT`.

Not delivered:

- OpenClaw, runtime, CLI registration, network, database, cache, session, LLM/NLP, embeddings, semantic search, global discovery, automatic admission, automatic placement, or sealed production module changes.

## Validation

- `python -m pytest -q reference/python/tests/test_hx1_trusted_host_bridge.py reference/python/tests/test_hx1_host_binding_preflight.py reference/python/tests/test_hx1_staged_outcomes.py reference/python/tests/test_hx1_receipt_regeneration.py reference/python/tests/test_hx1_boundaries.py`
  - Result: `55 passed in 8.03s`
- `python validation/hx1/run_hx1_validation.py --output validation/hx1/HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md`
  - Result: pass
  - SHA-256: `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`
- Fresh-process normal report SHA-256 checks:
  - Run 1: `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`
  - Run 2: `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`

## Report SHA Note

C2 normal report SHA-256 was `C7D81D6AD482BA38346643837AD69EA12E274CDB585B00D4A53579114F790CBF`.

C3 changes the receipt input fingerprint by adding the canonical DreamShard payload fingerprint. The normal scenario inventory and public stage outcome remain unchanged, but `execution_input_fingerprint`, `output_fingerprint`, and canonical receipt SHA necessarily change. The fixed C2 report SHA and the C3 requirement to bind complete DreamShard payload identity cannot both hold.

## Changed Boundaries

- Production code changes are limited to `reference/python/nollm/dream_geometry/host_execution`.
- Tests are limited to `reference/python/tests/test_hx1_*.py`.
- Documentation changes are limited to HX1 protocol, integration, delivery, validation, and roadmap files.
- Sealed implementation modules outside HX1 host execution were not modified.
