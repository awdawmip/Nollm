# CX2 OpenClaw Future Boundary

CX2 不接入 OpenClaw。本文件只记录未来若 owner 授权接入时 OpenClaw 必须作为 host 遵守的边界。

CX2 does not connect to OpenClaw and does not provide runtime code, hooks, API tokens, network calls, daemon config, or session integration.

If a future owner authorizes OpenClaw integration, OpenClaw must act as a host, not as hidden Core logic.

Future host duties would be:

- submit explicit CaptureRequest objects;
- hold or submit explicit promotion decisions;
- provide proposal and placement refs for admission;
- declare finite admitted worksets for assembly;
- submit query refs and budgets for recall;
- consume DI1 public envelopes;
- preserve CX2 non-inferences.

OpenClaw must not:

- bypass Capture / Promotion / Admission / Assembly / Recall boundaries;
- auto-admit from model text;
- perform global admission discovery;
- use embeddings or vector queries as Nollm recall;
- treat DG6 as recall influence;
- expose DG7 as production runtime.
