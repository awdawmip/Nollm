# DG7 Reference Runtime Positive Verification Report

## Verified Facts

- fresh Python process explicit A/B/C/D scenario: `completed`
- A/B capture status: `deferred`, then BA1/DA1 admitted and DF1 assembled
- C isolation: `captured/deferred only`, no AdmissionRecord, no snapshot/projection/envelope evidence
- D isolation: `admitted`, excluded from the explicit DF1 finite set and absent from DG6/DR1/DI1
- DG6 projection: lossless expansion matches `snapshot.replayed_traces` and does not affect DI1 recall
- DI1 envelope: exposes only A/B original DreamShard evidence and no geometry/trace/cover/gravity payload
- two fresh-process canonical receipt SHA-256: `f78ec9feb031759c2ce0aca023b3f9e809049f4a7cb63cb180b301e2a407c724`
- durable writes: limited to the explicit temporary work root and explicit receipt output

## Reasonable Inference

A controlled host integration can use this style of explicit runtime receipt without changing Core boundaries.

## Forbidden Inference

DG7 does not implement a production runtime, OpenClaw integration, automatic memory, semantic admission, persistent compression, global discovery, storage optimization, recall acceleration, or performance claim.

## Pending Research

- external host generation of Growth and Placement input
- stable transport adapter design
- session governance, configuration, cache, failure recovery, and user experience
- OpenClaw or other host integration as a separate owner decision
