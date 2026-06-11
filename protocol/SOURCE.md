# Source

Source records where a card claim came from. It helps Cortex separate remembered material from inference.

## Source Kinds

- `user_statement`: A direct user statement.
- `human_decision`: An explicit human decision.
- `project_file`: A source-of-truth project file.
- `ledger_event`: A ledgered Core event.
- `external_reference`: A cited source outside the notebook.
- `llm_inference`: A model-side inference or synthesis.

## Rule

LLM inference must not be recorded as confirmed fact without human review. It may be written as `draft`, `candidate`, `hypothesis`, or another clearly tentative form.

