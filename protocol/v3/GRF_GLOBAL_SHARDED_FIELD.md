# GRF Global Sharded Field

GRF7 extends local `RelationField` values with a metadata-only
`GlobalFieldDirectory`. A directory descriptor records profile, chart, layer,
cell/source ranges, counts, snapshot and ledger references, neighbors, and a
sparse bridge summary. It never stores Evidence content or semantic edges.

Each partition owns an independent `CellRegistry`, `PlacementIndex`, kernel
registry view, ledger, and snapshot. Exact profile and kernel definitions are
read-only shared definitions. The default partition strategies are spatial
cell range and source range; semantic entity clustering is not a default.

Global recall routes a typed identity to one partition, executes local recall,
and may follow only recorded cross-partition bridges. The caller must bound
partition hops, fanout, activation count, result count, profile compatibility,
and bridge confidence. There is no all-partition fallback scan.

Cross-partition stitches are auditable, reversible relation records. They do
not merge Evidence, rewrite sources, create facts, or bypass admission.
Repartition may move a placement or change its profile while preserving
Evidence and Admission identities and the source fallback reference.

Resident and logical-sharded scale are distinct measurements. A logical 10M
global field may keep all partition snapshots on disk while loading only the
bounded partition set required by a query. It must not be described as a
single resident 10M `RelationField`.
