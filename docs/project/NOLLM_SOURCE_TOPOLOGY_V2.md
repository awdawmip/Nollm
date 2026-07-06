# Nollm Source Topology V2

This topology classifies repository source by active V2 layer role.

## Normative Protocol

- `protocol/v2/LAYER_CONSTITUTION.md`: active layer constitution.
- `protocol/v2/LEGACY_BOUNDARY.md`: retired source and migration boundary.

## Core and Domain Source

- `reference/python/nollm/dream_geometry/`: V2 Core and deterministic domain
  source. It must remain free of terminal, adapter, OpenClaw, network, database,
  cache, LLM, NLP, embedding, semantic search, runtime activation, and global
  discovery dependencies unless a later task explicitly changes scope.

## Host Contract and Bridge Source

- HX1 assets are L4 Host Contract and Execution Bridge work.
- CX2 assets are L4 external cortex conformance and public envelope boundary
  work.

## Adapter Source

- HCG is accepted as an L5 File Capture Adapter.
- HAG1-C1R is accepted but unpromoted as an L5 File Admission Adapter candidate
  at `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`.

## Terminal and Product Source

Terminal or product work belongs to L6. It must enter Core through L5/L4 and
must not create private shortcuts into L0-L3.

## Retired and Migration Source

- V1, MT1, and pre-V2 prototypes: retired history.
- OpenClaw: frozen migration asset for future L5/L6 work.

Physical presence is not active status.
