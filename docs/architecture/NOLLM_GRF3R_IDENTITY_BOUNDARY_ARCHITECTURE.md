# NOLLM GRF3R Identity Boundary Architecture

`HostRequestID`, `EvidenceIdentity`, `PlacementIdentity`, and
`AdmissionIdentity` are distinct frozen value objects. Boundary JSON is parsed
into those types before `GRFHostService` dispatches a Core operation.

```text
Host mapping
  -> GRFHostRequest.from_mapping
  -> typed identity validation
  -> GRFHostService
  -> GRFFacade
  -> recall result with original source fallback
```

The File Adapter imports only the host contract. It neither imports nor owns a
GRF file store, placement policy, admission bridge, relation field, or recall
implementation. The terminal skeletons remain declarative capability files.
