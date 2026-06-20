# Nollm OpenClaw Sidecar Command Reference

Date: 2026-06-20

These commands are experimental internal sidecar commands. They are not a stable
public recall API and not an OpenClaw runtime plugin.

## `index`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. index
```

Parses `MEMORY.md`, optional `DREAMS.md`, and `memory/*.md`, then writes:

- `candidates.jsonl`
- `shards.jsonl`
- `geometry_marks.jsonl`
- `pending_writes.jsonl`
- `commit_ledger.jsonl`
- `sidecar_manifest.json`
- `openclaw_memory_sidecar_report.json`

## `search`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. search --query "memory search gravity report" --limit 5
```

Returns deterministic lexical matches with top-level follow-up identifiers:

```json
{
  "memory_id": "mem_...",
  "candidate_id": "cand_...",
  "shard_id": "shard_...",
  "source_path": "memory/2026-06-19.md",
  "line_range": [5, 12],
  "provenance": {
    "source_path": "memory/2026-06-19.md",
    "line_start": 5,
    "line_end": 12,
    "source_ref": "memory/2026-06-19.md:5-12"
  },
  "retrieval_score": 0.5,
  "gravity_report": {}
}
```

The command does not hard-filter by `drift_class`.

## `recall`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. recall --query "Atlas owner" --limit 6
```

Returns a model-facing digest with separated `direct_evidence`,
`lateral_context`, `cautions`, source path, line range, retrieval score, and
gravity report. The sidecar uses deterministic local lexical retrieval and
reports `candidate_source: "nollm_local"`.

## `get`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. get --id cand_...
```

Accepted id forms:

- `candidate_id`
- `memory_id`
- `shard_id`

The result returns source metadata, full text, geometry mark, and provenance.
When called after search or recall with an id from that result, it preserves the
same gravity report.

## `write-candidate`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. write-candidate --text "..." --source user
```

Writes only to `pending_writes.jsonl`. It does not mutate `MEMORY.md`,
`DREAMS.md`, or `memory/*.md`. Returned records include `durable_write=false`
and `target_files_mutated=false`.

## `commit-candidate`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. commit-candidate --candidate-id candidate_... --explicit-confirmation --target durable --reason "user confirmed" --source chat
```

Commits a staged pending candidate only with explicit confirmation. It appends a
deterministic Markdown entry to a Nollm-managed section of `MEMORY.md` or
`memory/YYYY-MM-DD.md`, records before/after hashes, appends `commit_ledger.jsonl`,
and returns `memory_core_reindex_required=true`.

## `status`

```bash
python scripts/run_openclaw_nollm_memory.py --repo-root ../.. status
```

Reports sidecar counts, source roles, accepted get id forms, manifest details,
and forbidden semantics flags.
