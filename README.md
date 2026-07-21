# Nollm

> Not an LLM. A notebook for LLMs.

Nollm uses a modular monorepo with explicit package ownership and public
dependency boundaries. Physical repository splitting is a separate concern.

The repository's single [active project basis](docs/project/ACTIVE_PROJECT.md)
links the architecture book, status, authorized task, progress ledger, and
latest baseline report without duplicating their revision-specific content.

## Active Runtime

- `nollm-core` owns semantic-blind `MemoryAtom`, addressed `AtomHandle`,
  deterministic geometry current state, atomic commands, generated-template
  lookup, explicit-cell bounded Recall, atomic state bytes, and the minimal
  immutable Trace port.
- `nollm-access` owns original Evidence, caller-held Handle registration,
  explicit Host/LLM/Human decisions, action mapping, and Evidence-backed Recall
  formatting.
- `nollm-snapshot` owns its state Protocol and service; `nollm-trace` owns all
  sink, JSONL, metrics, and inspector implementations.
- Bare and Minimal distributions use package APIs only.

Core operations require `GeometryAddress + local_atom_id`; there is no global
atom/source/topic lookup. Access never infers semantic placement with Python.
Architecture is the Index: Recall relationships come from cells, coverage,
lateral geometry, and explicit bounded bridges.

The active default physical profile uses source-centered translation-normalized
Coverage over signed-64 q/r, physical layers -64..64, `chart_id=default`, and
`phase=null`. Raw partition mass is validated before Q16. Access/OpenClaw expose
finite Surface and physical-entry pages, and the Host selects exactly one final
physical entry before Placement or Recall.

## Compatibility And Limits

`reference/python/nollm/grf` is a Legacy compatibility and regression baseline,
not the active Bare/Minimal runtime. The bounded OpenClaw P1 and restart-Recall
loop is capability-validated for the configured Windows Host and
`meituan/LongCat-2.0`; general corpus execution remains paused. This does not
prove general LLM placement quality. History and Audit remain skeletons,
and physical GitHub splitting remains deferred.

Evidence-first V2/V2.1/V2.2 and GRF8 are historical or superseded engineering
inputs. GRF8 is an engineering checkpoint, not accepted architecture.

## Validation

The bounded complete repository matrix is run from a clean committed source:

```powershell
.\tools\run_nollm_test_matrix.ps1 -RepoRoot (Get-Location).Path
```

Package, OpenClaw, Lab, boundary, and ownership checks may be run directly while
developing. `reference/python/run_tests.py` is a historical legacy-inclusive
diagnostic, not the active acceptance entrypoint.
