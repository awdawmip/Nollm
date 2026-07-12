# AOLD Human Review Queue

No human review is claimed in this stage. The existing 36 corpus decisions and the natural-chat live records are assistant-reviewed or unreviewed.

Representative cases for later human review:

| Case | Original | Model selection | Visible reason | Access result | Focus |
| --- | --- | --- | --- | --- | --- |
| 023 | Database backup schedule and retention | Exact source span | Durable operational schedule | Accepted | Whether one or two statements are preferable |
| 025 | Mobile and web release owners | Exact source spans | Independent ownership facts | Accepted | Split completeness |
| 030 | Archived reports immutable for 90 days | Exact source span after one retry | Durable retention rule | Accepted | Retry output quality |
| disabled-control | Retention statement while disabled | No selection | Tool unavailable | Not invoked | Lifecycle isolation |

Human reviewers may sign a later record with `review_type=human_review`, `reviewer_id`, `decision`, `review_note`, and `reviewed_at_utc`. Until then these remain assistant review candidates.
