# OCP3b Strict Live E2E Evidence

This package is a sanitized, committed audit subset for `ocp3b_20260620_141159`.

Conclusions: integration `supported`; tested-path safety `supported`; value hypothesis `inconclusive`.

Controls: the scored agents used `contextInjection: never`, fresh sessions, denied direct `read`, and used an isolated controlled corpus. `memory-core` remained the only memory-slot owner. Nollm remained a companion tool plugin.

The raw local runtime files stay under ignored `out/`; this folder contains the reproducible summaries and hashes needed by `reference/python/scripts/validate_ocp3b_live_e2e_evidence.py`.
