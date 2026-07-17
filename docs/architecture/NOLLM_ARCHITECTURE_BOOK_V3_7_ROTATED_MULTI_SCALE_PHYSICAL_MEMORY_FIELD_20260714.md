# Nollm Architecture Book V3.7: Rotated Multi-Scale Physical Memory Field

Date: 2026-07-14

Status: restored canonical architecture authority

## Physical Contract

Nollm geometry is a physical memory field, not a semantic index. A stored fact has one canonical `AtomHandle` at one `GeometryAddress`. Relations are observed through occupancy, lateral adjacency, bounded Coverage, and explicit reversible Stitch contracts. Position and path are never proof of factual truth.

Adjacent physical layers rotate by 22.5 degrees and scale by `beta = 2^(1/4)`. Increasing physical layer indices are finer. Physical layer and aggregation order are separate identity domains. The active product domain is the default chart, phase null, and `max(|q|, |r|, |q+r|) <= 2^31-1`.

## State And Ownership

Core owns canonical geometry addresses, occupied cells, Atoms, Coverage execution, and deterministic mutation. Access owns semantic decisions and validates only finite host-selected candidates. OpenClaw is the semantic Host. No source, topic, entity, query, Lens, or object-to-object route may become Core state.

One fact is stored as one Atom. Multi-entry reachability may emerge after later field growth, but it is observed through separate single-entry Recall operations and is not persisted as a fact-to-entry mapping.

## Active V3.7 Boundary

The active semantic write plane is physical layer 0 in `default_dream_v1/default`. Surface projections are finite, state-derived, and disposable. A write candidate is legal only when Core validates its address and Access validates its operation-local candidate identity. LLMs select supplied candidate IDs and never emit coordinates.

The historical route book remains scheduling context. V3.9 defines bounded approximate Coverage and V3.11 adds operation-local Recall Lenses and geometry-only Junction candidates without changing this physical contract.

