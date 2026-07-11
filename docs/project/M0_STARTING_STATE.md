# M0 Starting State

Recorded on 2026-07-11 before module ownership work.

- Branch: `codex/core-realignment-openclaw-live-integration`
- HEAD: `5f08ba6de6a0192ec6dcf7841acbfc1e0a0f8417`
- Paused work: resumable OpenClaw placement development batch 7.

The starting worktree contained:

```text
 M experiments/openclaw/results/placement_v2/results.jsonl
 M experiments/openclaw/results/placement_v2/run_state.json
?? experiments/openclaw/results/placement_v2/batch_7_summary.json
```

The files are model-run evidence, not credentials or machine caches. They were
preserved in the M0 starting checkpoint. M0 does not resume the live corpus.

Recent commits at capture time:

```text
5f08ba6d fix(openclaw): preserve corpus batch summaries
ec55a082 test(openclaw): continue placement development corpus
ffa207ee test(openclaw): continue placement development corpus
2a3d18ef test(openclaw): continue placement development corpus
22bbb8e1 docs(openclaw): record runtime discovery and operations
b06d2583 test(openclaw): continue placement development corpus
55d810ec test(openclaw): continue placement development corpus
e03b478f test(openclaw): start resumable placement development corpus
64736ca2 feat(openclaw): add resumable placement corpus runner
eb2ae152 test(grf): run 100k direct cell scale validation
```
