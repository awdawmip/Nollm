# GRF8 Real Data Ingestion

Use `GRFFacade.capture_source(path, recorded_at)` for Markdown, text, JSON,
JSONL, code, and chat logs. Repeating an unchanged file is idempotent. A
changed file creates only its new source-window shards. `retire_source()`
marks one source retired without removing unrelated evidence.
