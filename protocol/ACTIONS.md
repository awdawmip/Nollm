# Actions

Nollm actions describe the LLM-facing cognitive interface. They are protocol verbs, not runtime commands.

## Allowed Actions

- `orient`: Identify task context and candidate anchors.
- `surface`: List likely relevant anchors or cards without deep reading.
- `focus`: Select a smaller set of anchors or cards for recall.
- `recall`: Read selected Core records and assemble memory context.
- `write_card`: Propose or write a structured card according to policy.
- `link_cards`: Record explicit relationships between cards.
- `update_status`: Change lifecycle state through an auditable event.
- `append_ledger`: Append a ledger event for a Core change.

## Minimal Shapes

### `orient`

Input:

```yaml
query_or_task: string
known_context: string
```

Output:

```yaml
memory_intent: read_none | orient_only | surface | focus | write_candidate | ask_user_confirmation
candidate_anchors: []
warnings: []
```

### `surface`

Input:

```yaml
candidate_anchors: []
read_depth: shallow
```

Output:

```yaml
surfaced_anchors: []
surfaced_cards: []
warnings: []
```

### `focus`

Input:

```yaml
surfaced_cards: []
max_cards: integer
```

Output:

```yaml
focused_cards: []
excluded_cards: []
reason: string
```

### `recall`

Input:

```yaml
focused_cards: []
query_or_task: string
```

Output:

```yaml
recall_digest_address: string
recalled_points: []
source_addresses: []
do_not_assume: []
```

### `write_card`

Input:

```yaml
proposal:
  type: string
  status: draft | candidate
  claim: string
  anchors: []
  source: string
```

Output:

```yaml
card_id: string
status: draft | candidate
ledger_event: string
```

### `link_cards`

Input:

```yaml
from_card: string
to_card: string
relation: string
reason: string
```

Output:

```yaml
ledger_event: string
updated_cards: []
```

### `update_status`

Input:

```yaml
object_id: string
from_status: string
to_status: string
reason: string
human_approval: string
```

Output:

```yaml
ledger_event: string
status: string
```

### `append_ledger`

Input:

```yaml
event:
  op: string
  object_type: string
  object_id: string
  address: string
```

Output:

```yaml
event_id: string
timestamp: string
```

## Search

`search` may exist as an implementation helper, but it is not the primary cognitive interface. The preferred flow is anchor-oriented: orient, surface, focus, then recall.

## Core Boundary

Actions must preserve the Core/Cortex boundary. Cortex can request or propose actions; Core validates and records source-of-truth changes.
