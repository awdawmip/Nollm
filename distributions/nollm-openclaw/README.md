# nollm-openclaw

Composition target: `nollm-minimal` plus the Access-only OpenClaw adapter.
The active wire binds `default_dream_v1` / `nollm_rotated_physical_field_v1`,
uses one final Recall entry, and keeps Placement writes on physical layer 0.
OpenClaw never imports Core directly; Access owns Surface, Recall, and Placement.
