# HCG1 File-First Capture Gateway Validation Report

This report mirrors the HCG1 validation scope for machine-local delivery
evidence.

Validated behavior:

- host-explicit JSON capture through CI1 public values and HX1 public
  capture-only execution;
- source/session/persistent-explicit visibility reads through CI1
  `CaptureVisibility`;
- strict request decoding and unsupported mode rejection;
- deterministic reopen and drift rejection;
- no V1 CLI, OpenClaw, runtime, network, database, cache, field, assembly, or
  recall integration.

The full command results are captured in the final delivery receipt and TQ1-C7R
evidence capsule.
