# AOLD Invisible Dream Agent Live Report

Date: 2026-07-12

## Configuration

- Host: OpenClaw `2026.6.11` on Windows.
- Model mode: inherited `meituan/LongCat-2.0`.
- Round 1: `dream-v1`, shadow.
- Round 2: `dream-v2`, shadow.
- Round 3: `dream-v2`, statement-store.
- Main-chat concurrency: five; 15 unique sessions per round.

## Results

| Round | Main success | Dream started | Completed | Invalid JSON | Invalid schema | Writes/reopens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 15 | 15 | 12 | 2 | 1 | 0/0 |
| 2 | 15 | 15 | 12 | 3 | 0 | 0/0 |
| 3 | 15 | 15 | 11 | 3 | 1 | 11/11 |

All 45 starts occurred after the recorded main-reply delivery boundary and used
`deliver=false`. Additional visible messages were 0. Python semantic fallback
count was 0. Shadow rounds wrote no Store. Every round-3 statement id was
unique and reopened with the public `FileStatementStore.get` API with exact
field equality.

The `dream-v2` prompt removed the round-1 invalid-schema case in round 2, but
invalid JSON increased by one. Round 3 again had one invalid-schema output.
Therefore this gate establishes lifecycle, structure, and state boundaries,
not a general quality improvement or semantic-accuracy claim. Model failures
were fail-open and did not fail the ordinary chats.

Evidence replay:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python lab/nollm-lab/dream_agent/reports/verify_live_evidence.py
```

The compact evidence retains round metadata, chat receipts, plugin events,
canonical round-3 Store files, and the generated JSON summary. Raw CLI Host
envelopes and transient subagent transcripts are not retained.
