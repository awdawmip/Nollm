# Raw Event Protocol

Status: MT1 boundary.

RawEvents are archived observations of conversation or tool activity. MT1 does not implement runtime capture, but reserves the shape used by later takeover stages.

Fields:

- `raw_event_id`
- `kind`
- `session_id`
- `timestamp`
- `payload_ref`
- `content_hash`
- `visibility`

RawEvent records are archive inputs, not active recall answers.
