# V3.14 Remote Checkpoint

Branch checkpoint `be4123441b38fc6280fa986785371e2d90d68eaa` establishes the OpenClaw native memory-slot package skeleton: `kind: memory`, standard `memory_search`/`memory_get`, Memory Capability registration, and host tool-factory scope.

This checkpoint is intentionally incomplete. The full local implementation also contains Python bridge actions, exact current-Statement projection, hard final-render budget enforcement, and tests. Those changes are delivered in the accompanying Git Bundle and must be applied by the continuation task before Live or ClawHub acceptance.

Blocked/pending:

- packaged Windows sidecar;
- automatic Writer/capture migration;
- clean OpenClaw slot replacement Live;
- install/update/uninstall lifecycle;
- ClawHub validate/publish dry-run;
- complete regression and status/manifest updates.
