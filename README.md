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

## Compatibility And Limits

`reference/python/nollm/grf` is a Legacy compatibility and regression baseline,
not the active Bare/Minimal runtime. OpenClaw Live Integration and LLM corpora remain paused.
M1 does not prove LLM placement quality. History and Audit remain skeletons,
and physical GitHub splitting remains deferred.

Evidence-first V2/V2.1/V2.2 and GRF8 are historical or superseded engineering
inputs. GRF8 is an engineering checkpoint, not accepted architecture.

## Validation

The repository-wide diagnostic remains:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python run_tests.py
```

The command runs with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. It is a
legacy-inclusive repository diagnostic and not the primary V2 component acceptance gate.
Historical delivery acceptance used the TQ1 matrix and a parentless evidence capsule;
those terms do not define the M1 gate. M1 acceptance uses independent package
tests, boundary checks, GRF migration regression, and the explicit minimal E2E.
