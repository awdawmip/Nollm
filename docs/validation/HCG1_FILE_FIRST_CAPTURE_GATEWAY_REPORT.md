# HCG1 File-First Capture Gateway Validation Report

Scope: local file-first capture gateway using existing CI1 and HX1 public
contracts.

Current implementation adds:

- `nollm.dream_geometry.host_capture_gateway`;
- `reference/python/scripts/run_nollm_host_capture_gateway.py`;
- HCG1-only tests for capture/read behavior, boundaries, and CLI isolation.

Validation covered:

- HCG1-01 source-window capture and read;
- HCG1-02 deferred capture candidate publication;
- HCG1-03 persistent-explicit selected-shard read and dedupe;
- HCG1-04 context isolation and no fallback read;
- HCG1-05 deterministic same-input reopen;
- HCG1-06 drift rejection before additional write;
- HCG1-07 strict JSON shape, unknown field, and duplicate key rejection;
- HCG1-08 ephemeral/current-turn rejection before workspace write;
- HCG1-09 owned workspace marker and repo-root boundary rejection;
- HCG1-10 sanitized single-envelope error output;
- HCG1-11 source-level absence of hidden discovery/search/recall paths;
- HCG1-12 no registration on V1 CLI or OpenClaw/tool surfaces.
- HCG1-C1 canonical `kind/version/capture/policy` wire contract;
- HCG1-C1 legacy `capture_request/capture_policy` rejection;
- HCG1-C1 canonical read `result.shards` output;
- HCG1-C1 preservation of pre-existing `admission/keep.txt` and
  `cortex/keep.txt` bytes across success, reopen, and drift rejection.

Fixed gate status will be recorded in the delivery receipt after the full HCG1
gate set and final matrix complete.

Boundary statement:

HCG1 does not perform automatic admission, placement, geometry, field assembly,
semantic search, formal recall, OpenClaw integration, network service work,
database access, cache access, or runtime/session integration.
