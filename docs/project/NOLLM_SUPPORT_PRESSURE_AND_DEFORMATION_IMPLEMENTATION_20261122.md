# Support pressure and geometric deformation — implementation

Date: 2026-11-22.

This implementation follows the [design review](../architecture/NOLLM_SUPPORT_PRESSURE_AND_GEOMETRIC_DEFORMATION_REVIEW_20261122.md).
It provides a runnable native support-pressure/multilayer-write path and separate
Lab motion/deformation experiments. The native Core still uses its admitted
fixed Q40 geometry. The Lab float64 layer maps are explicit candidate geometry;
they are not installed as a replacement for a persisted Core field's geometry.

## Implemented components

| Component | Implementation | Actual behavior |
|---|---|---|
| Complete local incoming support | [Core incoming coverage](../../packages/nollm-core/src/nollm_core/incoming_coverage.py) | Inverts the current up stencil, checks at most nine candidate children, then uses their unchanged native up weights. |
| Public sample arithmetic | [Core sampled geometry](../../packages/nollm-core/src/nollm_core/sampled_geometry.py) | Exposes existing sample offsets, mapped stencil, nearest-cell rule and normalization for experiments. |
| Advisory pressure | [Access support pressure](../../packages/nollm-access/src/nollm_access/support_pressure.py) | Counts supplied current units and allocates lower support with exact integer Q16 arithmetic. |
| Explicit multilayer writes | [Write policy](../../packages/nollm-access/src/nollm_access/write_policy.py), [Access decision](../../packages/nollm-access/src/nollm_access/placement_contract.py) | The Host can select the experiment policy while retaining the existing Access transaction, binding and evidence path. |
| Native encounter integration | [Project memory](../../lab/nollm-lab/repository_memory/project_memory.py) | Offers scored placement candidates in explicitly selected physical layers and preserves the selected layer in actual writes. |
| Q40 motion reuse | [Lab motion](../../lab/nollm-lab/geometry/motion.py) | Reuses six-face margins, selectively recomputes crossings, or rebuilds the 96-point footprint. |
| Invertible candidate maps | [Lab deformation](../../lab/nollm-lab/geometry/deformation.py) | Similarity frames, passive reanchoring, physical pivot changes and compact radial twists. |
| Candidate-pressure comparison | [Lab pressure evaluation](../../lab/nollm-lab/geometry/pressure_evaluation.py) | Compares fixed material under candidate maps on the union of old/new influence regions, without modifying a field. |

No new bridge or object-relation index is introduced by these components.
Incoming shares, motion margins and comparison allocations are derived from
geometry. Existing bridge functionality remains separate from this experiment;
the functional pressure tests use native coverage and fields containing no
bridges.

## Pressure semantics and API

The continuous expression is

\[
P=1+99\frac{\max(D-S,0)}{D+\kappa},\qquad \kappa>0.
\]

The public score rounds half upward to an integer in 1–100. `D` is effective
material after the proposed additions; `S` is support allocated by the adjacent
finer layer. A physical layer's next finer layer is `layer + 1`.

`pressure_score(demand_units, support_q16, kappa=1)` uses integer material units
and support measured in units of 1/65536. For example, `pressure_score(8, 0)` is
89 and `pressure_score(8, 4 * 65536)` is 45. Kappa is a cold-start scale, not
invented evidence, and its default is an experimental choice rather than a
calibrated probability model.

`write_pressure(cell, units_at, additions=1, kappa=1)` returns a `WritePressure`
whose `to_mapping()` includes:

- `current_units`, `additions`, `demand_units`, and `support_q16`;
- `pressure`, complementary `write_weight = 101 - pressure`, and `advisory`;
- `demand_complete`, `support_complete`, `score_kind`, `unknown_cells`, and
  `geometry_error` when applicable.

The `units_at(cell)` callback supplies all current physical unit identities in
that cell. AtomHandles are appropriate identities. Repeated observations of an
identity count once. Reuse/supporting expressions and an in-place revision do
not create another Core atom. A distinct new placement does. The callback must
not present a partial list of a cell's units as its complete contents: return
`None` when that cell's current inventory is unknown.

Use `additions=1` to evaluate one proposed new placement and `additions=0` for
the current material, reuse or in-place revision. The project encounter's
candidate rows evaluate one proposed new placement. The caller retains its
ordinary consistent-read lease; project memory collects its pressure counts
under one Core operation lease.

Unknown lower supply is not zero supply. With known demand and incomplete
support, the score is an upper estimate and `score_kind` is `upper_estimate`.
Unknown demand produces no numeric score. A layer/storage boundary that prevents
complete coverage is also reported instead of being silently treated as empty.

Each lower unit retains its complete source-normalized up allocation. It can
support several upper cells fractionally, but its total allocation is one unit.
The caller must not renormalize only the visible recipients. Actual additional
lower material reduces the relevant support deficit; display rounding may
leave the integer score on a plateau. Reading the same material again does not
add supply.

The score is a reference for the Host. It does not reject a write, force a
descent, create lower content, or decide semantic placement or truth.

### Core incoming and sampling APIs

`incoming_coverage_candidates(parent)` returns the complete admitted candidate
tuple for the fixed up kernel. `incoming_coverage(parent)` filters that tuple
and returns members with `source`, `weight_q16` and `hit_count`, plus
`candidate_count`, `complete` and `unavailable_sources`.

Candidate completeness comes from the up stencil's inverse bounds, not the
parent's separately sampled down footprint. The known witness
`L0(67,5) <- L1(94,-30)` is retained by this path even though the parent's down
footprint omits that child. The at-most-nine bound belongs to this fixed kernel;
it is not a bound for arbitrary deformed grids.

The public arithmetic names exported by `nollm_core` are `CoverageStencil`,
`coverage_stencil_q40(source, direction)`, `coverage_sample_offsets_q40()`,
`nearest_axial_q40(q, r)` and `normalize_q16_weights(counts)`. The mapped stencil
contains `direction`, `center_q40` and `offsets_q40`. These are existing arithmetic
inputs and operations. Raw transformed coordinates still require the caller's
applicable geometry/storage-domain interpretation.

## Native multilayer writing and encounter

The old default policy remains
`nollm_default_dream_layer0_safe_write_v1`. Explicit experimental decisions select
`EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID`, whose value is
`nollm_default_dream_multilayer_experiment_write_v1`:

```python
from nollm_access import AccessDecision, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID
from nollm_core import GeometryAddress

decision = AccessDecision(
    "lower-placement", "statement-id", "new",
    target_cell=GeometryAddress("default_dream_v1", "default", 1, 0, 0),
    reason_text="Host selected this lower cell after observing the locality.",
    write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
)
```

The selected policy retains the default profile/chart/phase and writable radius.
GeometryAddress already defines the admitted physical layer domain. Actual
capture/apply, revision, move and source recovery use the existing Access runtime;
the new policy does not introduce another data store or persistence schema.

The Python project interface accepts:

```python
encounter(field, layers=(0, 1, 2))
encounter(field, choices=(shown_id,), cursor=previous_cursor)
decide(field, cursor, "new", shown_cell_id,
       note_id="new-id", body="Host-authored statement", sources=[source_reference])
```

The first call selects the physical scope; later calls retain it in the cursor.
Changing scope within an existing encounter requires a restart. Locality output
includes `physical_layers`, `write_policy_id` and `cells[].write_pressure`.
Candidates include native Junction results, in-scope adjacent Coverage targets,
and complete incoming-up sources. A terminal choice uses a currently shown
candidate and keeps its actual layer. Reuse/revision uses the policy already
selected by the cursor. Each new encounter starts with its requested scope;
scope is not silently made a permanent field setting.

### CLI examples

Run these commands from a Nollm Git checkout. Choose a fresh field/cursor path
for the experiment. The runtime also remains installable using the existing
`install_skill.py`; the installed `scripts/memory.py` accepts the same project
commands.

Start a native encounter:

```bash
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field /tmp/nollm-pressure-field encounter \
  --cursor-file /tmp/nollm-pressure-session.json --layers 0 1 2 --via vertical
```

Read the returned candidates and pass a displayed candidate ID as the positional
choice on the next call. Continue until `kind` is `locality`. The Host then
chooses one displayed placement ID, such as `cell:1:0:0` when it is actually
shown. A terminal command uses the existing cursor and does not repeat
`--layers` or change the budget:

```bash
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field /tmp/nollm-pressure-field encounter \
  --cursor-file /tmp/nollm-pressure-session.json \
  --new cell:1:0:0 --id geometry.support.v1 \
  --repo . --cite 'README.md#L15-L25' <<'TEXT'
The Host chooses semantic placement while Core executes native geometry.
TEXT
```

The chosen ID must come from that encounter's displayed locality. A successful
terminal choice removes its disposable cursor. Start another encounter to make
another decision. High pressure does not redirect a valid explicit same-layer
choice.

For an explicitly selected direct placement, the existing `save` command also
supports nonzero layers:

```bash
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field /tmp/nollm-pressure-direct save geometry.lower.v1 \
  --at 0 0 --layer 1 --experimental-multilayer \
  --repo . --cite 'README.md#L15-L25' <<'TEXT'
Native cross-layer coverage connects physically placed material to original evidence.
TEXT
```

Without the explicit experimental flag, direct semantic writing keeps its L0
policy. Direct revision of a nonzero-layer current statement similarly selects
the experimental policy. `save_statement` has the corresponding keyword
arguments `layer=0` and `write_policy_id=ACTIVE_SEMANTIC_WRITE_POLICY_ID`.

## Lab motion and layer maps

### Exact Q40 translation reuse

`TranslationFootprint.from_source(source, direction)` constructs a reusable
footprint. `translate((dq_q40, dr_q40), mode="auto")` returns a `MotionStep` with
the new footprint, selected mode, nearest-cell call count and changed-sample
count. `mode="full"` is the full 96-point comparison path.

Use the returned footprint for the next sequential movement. The implementation
keeps even whole-cell anchors, preserves the original half-even/cube-repair
rules, and refreshes its margins after crossings. `counts_q16()` returns sorted
`(q, r, hit_count, weight_q16)` records. `next_boundary(direction_q40)` returns an
exact Fraction for the first possible crossing, or `None` for zero motion.

The selection of reuse, crossing updates or full rebuild affects computational
work, not the output semantics. Its contract is
`lab_q40_translation_reuse_v1`. It does not change Core state or improve the
underlying quadrature's real-area accuracy.

The read-only CLI compares the two paths directly:

```bash
python3 lab/nollm-lab/geometry/deformation_cli.py motion \
  --source 0 19 -17 --direction coverage_up --delta-q40 1 -1
```

### Similarity, passive reanchor and radial twist

`SimilarityFrame` expresses
`world = origin + scale * R(angle) * (local - local_anchor)`; angles are radians.
`reanchor()` changes that expression while preserving physical points.
`rotate_about(center, angle)` performs an actual world-space rotation.

`RadialTwist(center, radius, angle)` uses the compact C1 angle profile
`angle * (1 - r²/radius²)²` inside its radius and zero outside. Its inverse uses
the negative angle at the same radius. The analytic map preserves area and
transforms a whole layer continuously. `with_center()` changes its physical
center and therefore generally changes the map.

`LayerMap(frame, twists)` applies the similarity followed by the ordered
world-coordinate twists. Its inverse reverses that order. `LayerMap.for_layer(l)`
constructs the default ideal similarity in float64. Maps expose ordinary
`to_mapping()`/`from_mapping()` JSON representations. `sampled_coverage(source,
target_layer, source_map, target_map)` applies the target inverse to transported
source samples for one adjacent layer.

Example:

```bash
python3 lab/nollm-lab/geometry/deformation_cli.py coverage \
  --source 0 1 0 --target-layer 1 --twist 0 0 6 0.8
```

`--source-map` and `--target-map` accept JSON LayerMap files. `--twist` appends a
physical target-map twist. `--reanchor X Y` passively changes the target frame's
local anchor; it does not request a physical relocation.

The deformation contract is `lab_float64_layer_map_quadrature_v1`: float64 maps
followed by Q40 sample classification and Q16 normalization. It is distinct from
the fixed integer production transform. Selected fixtures are compared with an
independent high-precision calculation; this does not establish bitwise
equivalence for every coordinate or certify curved-cell real overlap areas.
Actual Core writes/recall continue using the original geometry.

## Compare candidate geometry without persisting a move

`evaluate_pressure()` and `compare_pressure()` take explicit material counts
for one adjacent layer pair. `compare_pressure()` retains fixed material and
compares candidate maps on the union of the old and new affected regions. It
reports per-cell pressure, source-normalized allocations, changed coverage,
deficit differences and the maximum known pressure. It does not approve a move,
write a field, or infer semantic placement.

This example is a complete, deliberately small finite fixture:

```bash
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src:lab/nollm-lab \
python3 - <<'PY'
import json
from nollm_core import GeometryAddress
from geometry.deformation import LayerMap, RadialTwist
from geometry.pressure_evaluation import compare_pressure

def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)

upper = {cell(0, 1, 0): 4}
lower = {cell(1, 1, 0): 4}
candidate = LayerMap.for_layer(1).with_twist(
    RadialTwist(center=(0.0, 0.0), radius=6.0, angle=0.8)
)
report = compare_pressure(
    upper, lower, upper_layer=0,
    after_lower_map=candidate,
    inventory_complete=True,
)
print(json.dumps({
    "contract_id": report["contract_id"],
    "delta": report["delta"],
    "coverage_changes": report["coverage_changes"],
    "advisory": report["advisory"],
}, indent=2))
PY
```

`inventory_complete=True` is a caller declaration that these dictionaries cover
the entire finite inventory of this selected adjacent pair. It is not a claim
that the evaluator scanned a whole live field. Counts for supplied cells must
be accurate. With the default partial inventory, omitted upper demand remains
unknown and supplied lower support is a lower bound; total-field improvement
is not claimed. `total_deficit_q16` is `None` until completeness is declared.
Even a complete result concerns this pair and this sampled geometry contract,
not a total over all physical layers or a semantic recall-quality measure.

`evaluation_cells` may add cells but cannot remove supplied upper cells or lower
recipients. The before/after union prevents apparent improvement from moving a
deficit outside the evaluated window. Total deficit and pressure distribution
remain separate diagnostics: redistribution can change the latter while
preserving the former. Source support stays conserved in both cases.

An executed fixture in `test_same_total_deficit_can_have_a_better_pressure_distribution`
places ten upper units in each of `(0,0)`, `(0,1)`, `(1,-1)`, `(1,0)` and eight
lower units at `(0,0)`. Both candidate maps initially use the identity frame;
the lower map then shifts by `sqrt(3)/2` along world x. The before/after
pressures in that order are `[19,91,91,91]` and `[61,85,85,61]`. Total deficit
stays `2097152 Q16` (32 units), allocated supply stays `524288 Q16` (8 units),
and maximum pressure falls from 91 to 85. This is a controlled geometry example,
not an automatic decision to relocate a live field.

## Validation and reproduction

Run the functional slice from the repository root:

```bash
python3 lab/nollm-lab/geometry/run_support_deformation_tests.py
```

The [runner](../../lab/nollm-lab/geometry/run_support_deformation_tests.py) uses
stdlib `unittest`, temporary fields and temporary Git repositories. It does not
modify the user's maintained 速记本 or installed skills. The completed integrated
run passed **63 tests**:

| Suite | Tests | Main observation |
|---|---:|---|
| Core incoming coverage | 6 | Wider-scan completeness, the nonreciprocity witness, boundaries and source shares. |
| Access support pressure | 10 | Score properties, duplicate observations, conserved supply and unknown inventory. |
| Experimental multilayer Access | 8 | Default policy, actual persistence, revision/reuse and cross-layer move bindings. |
| Project pressure | 7 | Real pressure feedback, cursor continuation, checkout CLI and isolated installed runtime. |
| Q40 motion | 7 | Full-reference equality, sequential reuse, ties, signed coordinates and parity. |
| Lab deformation | 10 | Inverse maps, area/Jacobian checks, passive/physical anchors, independent finite references and CLI. |
| Candidate-pressure evaluation | 8 | Conserved allocation, region union, relative/common deformation and partial inventory. |
| Existing project encounter | 5 | Prior one-entry semantic choices, preview behavior and fresh-process continuation. |
| Existing project memory | 2 | Existing installed-field, source, revision and runtime-replacement behavior. |

The motion CLI example above returned `mode="reuse"`, `round_calls=0`,
`full_round_calls=96`, `changed_samples=0` and `matches_full=true` in this run.
Those counts describe this particular small step; they are not a wall-time
speedup claim for arbitrary motion or twist.

The source tests and runner are the reproducible verification material. Their
temporary fields prove actual writes and reads in this slice. They do not
establish a deployed variable-geometry provider, a formal real-area theorem,
or improved semantic recall quality on uncontrolled tasks. Those remain
separate research/implementation questions.
