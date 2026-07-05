# Nollm Engineering Gravity RC Test Shards

Date: 2026-06-19

Test shards exist to make RC maintenance failures easier to locate. They are
diagnostic runners, not product behavior and not evidence for or against the
memory hypothesis.

List profiles from `reference/python`:

```bash
python scripts/run_nollm_test_shards.py --list-profiles
```

Fast smoke profiles:

- `collect`: pytest collection only.
- `core`: stable Core/reference CLI tests.
- `docs`: documentation and repository hygiene tests.
- `shard_smoke`: one tiny shard-runner smoke test for review-safe subprocess checks.

Dream diagnostics:

- `dream_pipeline`: dream shard, placement, pipeline, and parameter tests.
- `dream_reports`: dream report, golden, batch, regression, and suite tests.
- `dream_gate`: gate/package diagnostics that do not invoke shard-runner self-tests.
- `shard_runner`: shard-runner self-tests kept separate to avoid recursive shard execution.
- `dream`: compatibility aggregate for the three dream diagnostic profiles.

Broad profile:

- `full`: the existing legacy single-process full test runner.

These profiles are curated diagnostics from the engineering RC period. They are
not a current complete-suite proof for the full repository after later Dream
Geometry, HX1, and TQ1 additions. Use the TQ1 bounded complete test matrix for
delivery-grade proof that every fresh pytest node id ran exactly once.

Shard reports are runtime artifacts under `out/nollm_runtime/test_shards/`.
Timeouts are diagnostic failures. A timeout means a shard needs triage; it does
not prove that Nollm is scientifically wrong.
