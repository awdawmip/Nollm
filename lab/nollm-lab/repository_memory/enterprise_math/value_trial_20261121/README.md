# Research-memory value development trial — 2026-11-21

Start with [REPORT.md](REPORT.md). This directory is a public development diagnostic, not a held-out benchmark or formal mathematics acceptance.

The subsequent [navigation, cross-line and revision trial](followup/README.md) includes the resumable runtime and the field actually used by the new readers.

## Contents

- [CASES.md](CASES.md): the identical A/B/C questions given to three fresh-history readers.
- [GOLD.md](GOLD.md): load-bearing obligations frozen before execution; now public.
- [quality-review.md](quality-review.md): independent answer assessment, with its actual independence limits.
- [metrics.json](metrics.json): primary successful read outputs and explicit unknown overhead.
- `S/`, `F/`, `N/`: actual answers and full successful tool-output traces. S also includes its extra trace-read disclosure.
- [method-review.md](method-review.md): experimental method review and primary literature references.
- `architecture/`: actual synthetic navigation script, measurements and code audit.
- `runner.py`, `prepare.py`, `corpus-manifest.json`, `flat.json`: minimal trusted-input reproduction aids. No new runtime service or defensive framework.

## Three reader routes

S can list source titles/line counts, find literal terms, and read source windows. F can browse all current memory previews, use freely reformulated literal searches, read notes and sources. N uses Surface choices to select a physical entry, bounded native recall, then note/source expansion; using literal search would be disclosed as a mixed run. The flat export has exactly the same current statements, source references and retained history as the native field. No correct entry coordinates are given to N.

All three readers got the same cases and foundation scope, with A/B/C in sequence. They inherited the same parent model and no prior conversation turns. The model/API revision, reasoning tokens, cache usage and billing are not exposed. The filesystem/tools were shared, so reader restrictions were instructions, not technical isolation. Question families and explicit cross-line bridges already existed in development materials.

The parent performed canonical global/project startup once and supplied the applicable scope to the readers. The common startup, instructions and task-design cost are not in primary read metrics. Each agent was told to use the runner for all new scientific content, avoid other answers/GOLD/reports, keep the field read-only, and disclose failures or fallback. All three followed the stated scientific-material route; S separately reprinted its own log, which is recorded as unmetered repeated-input overhead.

## Reproduce locally

Use an already available source checkout containing Enterprise Math `f16294a5a7ffa435a32b70214d881fd4450eb494` and the installed Nollm runtime/seed at `ddf7dc00b2cea43dccc5d783d20aa88e21de4e0b`. `prepare.py` reads local Git objects; it does not fetch a repository. Remote acquisition follows the applicable environment's authorized GitHub transport. The original run acquired the manifest files through the connected GitHub file API and wrote an equivalent local config.

```sh
python prepare.py --runtime /path/to/scripts/runtime --field /path/to/seed/field --source-repo /path/to/enterprise-math --out /tmp/nollm-value-run
python runner.py --config /tmp/nollm-value-run/config.json --arm N --case A --log /tmp/nollm-value-run/N/reads.jsonl walk
python runner.py --config /tmp/nollm-value-run/config.json --arm F --case A --log /tmp/nollm-value-run/F/reads.jsonl catalogue
python runner.py --config /tmp/nollm-value-run/config.json --arm S --case A --log /tmp/nollm-value-run/S/reads.jsonl catalogue
```

Give each new reader CASES and only its route. A reader chooses its own queries and reasoning; there is no target coordinate, fixed thinking sequence or artificial query quota. `source` accepts a pinned `commit:path#Lfirst-Llast`; `read` accepts path, first and last line. The trusted runner reads the fixed local corpus named in config; it is not a general source-authority resolver or access-control boundary. All references in this run used the frozen manifest revision.

The runner logs successful material outputs and time inside its operation, excluding imports/process startup and failed operations. Its raw line-window helper raises a normal indexing error for an excessive end line; the current trial reports those errors. This helper is separate from the deployed source endpoint and does not prove a deployed defect. For a future total-cost measurement, record all tool returns, failure outputs and actual usage when available. Do not retroactively invent missing costs for this run.

The synthetic geometry diagnostic has its own method and timing scope in `architecture/ARCHITECTURE_AND_SCALE.md`; do not combine its oracle reachability results with model semantic performance. Original full scientific source files need not be copied into Nollm: the manifest pins their owning repository and this directory retains the exact windows actually consumed.

The implementation task and Codex prompt are in [`docs/project/tasks/`](../../../../../docs/project/tasks/NOLLM_RESEARCH_VALUE_TESTS_20261121.md). Follow current project entries when implementing a candidate; preserve this baseline and compare actual behavior rather than treating this directory as a new global gate.
