# DC1 Legacy Reopen Fixture

The DC1.1R tests use a frozen legacy artifact shape embedded in
`tests/test_dc1_cortex_compiler.py`.

Fixture provenance:

- generated to match the pre-DC1.1 DC1 compiler contract at
  `3654c67cf065646e2c3a0c2247f4c73da26597e7`;
- proposal and receipt omit `possible_conflict_refs`;
- receipt `input_snapshot` preserves the raw old submission shape;
- the proposal includes legacy rule-label variance and old budget caps so the
  current reopen path must mark it `legacy_dc1_read_only`;
- the fixture is synthetic only and uses the DE1 synthetic fixture in the DC1
  tests.

The compatibility path must never rewrite these artifacts or treat them as a
new `current_dc1_1` submission.
