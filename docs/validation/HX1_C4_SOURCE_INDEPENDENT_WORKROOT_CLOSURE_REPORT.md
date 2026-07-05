# HX1-C4 Source-Independent Work-root Containment Closure Report

HX1-C4 verifies that work-root containment no longer depends on caller cwd.

Validated boundary:

- HX1 protects the source repository root discovered from the HX1 module path.
- HX1 also protects the repository root discovered from caller cwd when one exists.
- Detection uses pathlib-only `.git` file or directory ancestor checks.
- External temporary owned work-roots remain valid.
- No git, subprocess, shell, network, environment discovery, OpenClaw, runtime, LLM/NLP, daemon, cache, database, global discovery, automatic admission, or sealed production module change is introduced.

The normal HX1 validation report remains byte-identical with SHA-256 `07DA392EA50A5E6B6F467C24225024F3A71F6B25EF1883CFA49EC688961E1135`.
