# Status

Nollm statuses describe the lifecycle of Core objects. Status is auditable state, not model confidence.

## Allowed Statuses

- `draft`: Proposed but not ready for use.
- `candidate`: Plausible and reviewable, but not confirmed.
- `confirmed`: Currently accepted as stable within the notebook.
- `superseded`: Replaced by a newer card or object.
- `rejected`: Preserved as rejected, with reason.
- `archived`: Readable history, not surfaced by default.

## Transition Rules

- LLM/Cortex may propose `draft` or `candidate`.
- `confirmed` requires explicit operator approval in v0.1.
- `superseded` must reference the replacing card or object.
- `rejected` must preserve the rejection reason.
- `archived` remains readable but should not be surfaced by default.

## Core Boundary

Core records status and validates transitions. Cortex may recommend a transition, but it must not silently promote or mutate Core state.

`confirmed` does not mean factually true, permanently correct, or human oracle truth. It means the record is currently accepted as stable enough for normal notebook use. Later evidence, ledger events, or corrections may supersede it.
