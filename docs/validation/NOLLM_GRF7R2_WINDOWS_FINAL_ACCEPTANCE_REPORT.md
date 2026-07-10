# GRF7R2 Windows Final Acceptance

## Scope

GRF7R2 closes durable adapter-owned HostRequestRegistry recovery, explicit
negative bridge verification, sustained mutation semantics, and external raw
evidence handoff. The adapter registry records ownership and retry metadata;
it is not an Evidence truth source.

## Evidence

`experiments/grf/results/grf7r2/GRF7R2_GATE_EVIDENCE.json` is computed from
the Windows external evidence root. Gate A replays the durable registry across
adapter restarts. Gate B checks 1,000 individual forbidden-bridge queries,
with 250 each for rejected, decayed, rolled-back, and mixed controls. Gate C
computes one million event counts, identity and duplicate checks, recovery,
snapshot replay, Windows RSS, tracemalloc, object count, ledger bytes, and
snapshot bytes from the sustained-workload outputs.

The observed retained state is separately measurable through the 1M event
ledger, workspace objects, durable registry, tracemalloc, and Windows process
RSS. It is classified as retained-state growth for this bounded run rather
than an unmeasured leak; the raw samples remain in the evidence pack.

Cross-platform portability was not validated in this stage.

## Delivery Boundary

The final Git bundle, evidence pack, and delivery receipt are generated outside
the repository. The receipt binds the actual final HEAD and byte hashes, while
the Git-tracked manifest binds producing and report commits without claiming a
self-referential final bundle hash.
