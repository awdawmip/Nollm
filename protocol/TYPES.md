# Types

Card type tells Cortex how to use a memory. Type is not status, trust, or source.

## Allowed Types

### `fact`

- Meaning: A durable statement about the project or world.
- Write when: The statement is source-backed and useful for future recall.
- Cortex use: Recall as information, subject to status and trust.
- Must not infer: That related unstated facts are also true.

### `decision`

- Meaning: A choice that should guide future work.
- Write when: A human chooses a direction.
- Cortex use: Treat confirmed decisions as constraints on future proposals.
- Must not infer: That the decision is permanent or universal.

### `definition`

- Meaning: A canonical meaning for a project term.
- Write when: A term needs stable interpretation.
- Cortex use: Use to reduce ambiguity during orientation.
- Must not infer: That the term defines a full ontology.

### `constraint`

- Meaning: A boundary that limits allowed behavior.
- Write when: Something must not be done or must be preserved.
- Cortex use: Apply before proposing actions or writes.
- Must not infer: That all adjacent behavior is forbidden.

### `preference`

- Meaning: A preferred style, choice, or tendency.
- Write when: Preference is durable enough to affect future work.
- Cortex use: Prefer it when no stronger decision or constraint conflicts.
- Must not infer: That preference overrides explicit instructions.

### `warning`

- Meaning: A risk or caution.
- Write when: A recurring mistake or hazard should be surfaced.
- Cortex use: Surface before risky writes or interpretation.
- Must not infer: That the warned action is always prohibited.

### `failure`

- Meaning: A recorded failed attempt or bad outcome.
- Write when: The failure should prevent repeated work.
- Cortex use: Recall during planning and troubleshooting.
- Must not infer: That the approach can never work under changed conditions.

### `procedure`

- Meaning: A repeatable process or checklist.
- Write when: A workflow should be followed again.
- Cortex use: Use as guidance, not hidden automation.
- Must not infer: That execution is authorized without user intent.

### `question`

- Meaning: An unresolved issue.
- Write when: The project needs to preserve uncertainty.
- Cortex use: Surface as open context.
- Must not infer: An answer.

### `hypothesis`

- Meaning: A plausible but unconfirmed explanation or proposal.
- Write when: The idea may guide investigation.
- Cortex use: Treat as tentative.
- Must not infer: That it is confirmed fact.

### `evidence`

- Meaning: A record of support for another card or claim.
- Write when: Evidence should be independently addressable.
- Cortex use: Cite when supporting claims.
- Must not infer: That evidence alone settles conflicts.

### `note`

- Meaning: General useful context.
- Write when: Context matters but does not fit a stronger type.
- Cortex use: Recall cautiously.
- Must not infer: That a note is a decision, fact, or constraint.

