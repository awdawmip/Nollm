# Support pressure and geometric deformation — design review

Date: 2026-11-22. Scope: Nollm research and design.

Status: the user's direction is recorded below; formulas and algorithms are
reviewed candidates. This document does not activate a new write policy,
deformation API, coverage contract, or stored-data migration.

Inspected implementation: `awdawmip/Nollm@e31a912fa283c5bca88c5f023b25d01c85e1bf28`.
The small mathematical probes used that unchanged source. Production code,
working memory and existing bridge state were not modified for this review.

## 1. Current user direction

The user requested a support-pressure mechanism: material in the finer layer
supports writes in the coarser layer. Continued writing where finer-layer
support is insufficient should raise the incentive to explore downward. The
user explicitly corrected compulsory descent to advisory exploration pressure,
with a 1–100 reference score for candidate writing layers.

The geometric goal extends beyond rotation, scaling and stitching to twisting,
changing anchors, and fast decisions about relocation. Relationships should
continue to arise from native coverage. New object-to-object bridges, graph
routes or vector-neighbor relations are not the mechanism for this work.

The preceding suggestion to prioritize relocation plus bridge maintenance was
too narrow for this direction. Existing BridgeSpec/recall support is an
implementation fact, not the design target for the deformation mechanism.
Existing stored bridges have not been deleted by this review.

## 2. A local, advisory pressure score

Evaluate a candidate physical cell at each locally considered layer, not the
total volume of an entire infinite layer. Larger physical layer indices are
finer: the next lower layer of L is L+1.

For candidate cell c, let D(c) be its effective current material count after the
proposed write. Let S(c) be actual current material in the adjacent finer layer,
apportioned to c through native coverage. A first candidate is

\[
P(c)=\operatorname{round}_{1/2\uparrow}
\left(1+99\frac{[D(c)-S(c)]_+}{D(c)+\kappa}\right),\qquad\kappa>0.
\]

Here [x]+ means max(x,0). Before rounding the range is [1,100); the displayed
integer lies in 1–100. Kappa controls cold-start scale and is not fictitious
support. Kappa=1 below is illustrative, not calibrated. Count units and the
desired amount of support per upper unit remain explicit modeling choices.

| D after proposed write | S | Pressure, kappa=1 |
|---:|---:|---:|
| 1 | 0 | 51 |
| 4 | 0 | 80 |
| 8 | 0 | 89 |
| 8 | 4 | 45 |
| 8 | 8 | 1 |
| 9 | 8 | 11 |

In the deficit region, the continuous score has derivatives

\[
\partial_D P=99(S+\kappa)/(D+\kappa)^2>0,\qquad
\partial_S P=-99/(D+\kappa)<0.
\]

Thus more unsupported material raises pressure; more lower support reduces it.
Integer rounding necessarily creates plateaus. If a UI needs a positive
write-preference scale, W=101-P is the same signal in the opposite direction,
not an additional independent score or a calibrated probability.

Pressure is advice to the Host. It neither rejects writes nor creates a duty
to write, descend, manufacture lower-level material, or reach pressure one.
Geometric material support is not logical corroboration or a truth score.

### Count material once; conserve its allocation

For unique current lower-layer units m, define

\[
S(c)=\sum_m\mu(m)\,a(d(m),c),\qquad
a(d,c)=w^\uparrow_{d,c}/65536.
\]

The simplest trial uses mu(m)=1 per active canonical atom. Re-reading the same
binding through several paths, historical versions and supporting expressions
does not manufacture more atoms. Semantically duplicated propositions with
different IDs still require Host reuse/revision judgment; identity deduplication
does not solve semantic duplication. Raw token length is a poor default unit.

The source is each lower cell's already-normalized coverage_up. One lower
unit's contributions sum to one over all its upper targets. Counting the whole
unit once for every overlapping upper cell would multiply support. Do not
renormalize only the targets visible in a particular encounter. Deduplicate
units before allocation, while retaining their legitimate fractional
contributions to different upper targets.

This treats material as distributed across its cell according to native
coverage. It is a proposed spatial-allocation model, not evidence that every
lower proposition semantically supports every intersecting upper proposition.

The current example L1(-7,5) distributes one unit to four upper cells with Q16
weights 1365, 55979, 6827 and 1365, whose sum is 65536. Twenty observations of
that same unit still supply one unit, not twenty or eighty.

### Avoid recursive and observational artifacts

S uses actual adjacent occupancy, never other pressure scores. Read-only
exploration cannot itself create support. Compare candidate cells after the
same proposed write: an empty candidate at any depth has pressure 51 under
the illustrative parameters, not a free zero-pressure advantage at every
deeper layer. This removes that scoring artifact; the Host still decides the
useful evidence granularity and when further exploration has no value.

Unobserved support is not known absence. If only a subset is available,
P(D,S_observed) is an upper estimate of pressure for fixed D. Preserve the
incomplete-support status instead of claiming a complete local count.

## 3. Complete lower candidates without a reverse relation index

Current sampled coverage_up and coverage_down are not reciprocal enumerators.
At L0(67,5), coverage_down returns five children, but omits L1(94,-30), whose
coverage_up hits that parent with hit_count=1 and weight_q16=683.

For the unchanged current up kernel, let S0=2^40, M be its integer axial
matrix, o_j its 96 compiled offsets, n a child address and u a parent address.
Let H be the closed unit axial hexagon:

\[
H=\{z:|2q+r|\le1,\ |q+2r|\le1,\ |q-r|\le1\}.
\]

A child sample can hit u only if

\[
Mn+o_j-S_0u\in S_0H.
\]

For each row a of M inverse, precompute

\[
\ell_a=\min_{v\in S_0H}a v-\max_j a o_j,\quad
b_a=\max_{v\in S_0H}a v-\min_j a o_j.
\]

The complete coordinate candidate interval is
[a S0 u + ell_a, a S0 u + b_a]. Hexagon extrema need six vertices; offset
extrema are fixed once per template. Enumerate integer coordinates with
ceil(lower) through floor(upper), including equality. Filter candidates using
the original coverage_up rounder and read occupied candidates directly.

Exact interval widths for the current kernel are

\[
\frac{749859300844844993802146}{284946548333783909500051}<3,
\qquad
\frac{2249577902535352092961766}{854839645001351728500153}<3.
\]

Consequently at most 3×3=9 child cells are candidates for any parent under this
fixed kernel. This is a template-derived bound, not a bound inferred from
random tests. The witness above has candidate box [93,95]×[-32,-30], containing
six actual incoming children. Domain-boundary/storage rules still apply.

No incoming-edge table is needed. Different future deformation families need
their own inverse-region bounds; the nine-cell result is not automatically
valid for arbitrary twists or highly stretched cells.

## 4. Geometry changes and anchor meanings

Represent each layer's physical map by Phi_l. A source point enters target
coordinates through

\[
T_{s\to t}=\Phi_t^{-1}\circ\Phi_s.
\]

Pure coordinate reanchoring changes representation while preserving physical
cells. Applying the same coordinate transform F to both maps cancels in the
relative map. It does not relieve an actual spatial support deficit.
Rounding a fractional reanchor to integer addresses can move cells and is not
the same operation.

Moving atoms on a fixed grid changes occupancy. Moving/rotating/scaling one
layer changes relative coverage. Changing a twist's physical center generally
changes the field. These operations should not be conflated with historical
semantic anchor_fields or bridge endpoint GeometryAnchor objects.

Common invertible affine transformations preserve overlap area fractions
because their Jacobian determinant is constant. A general common nonlinear
map preserves set intersections but changes Euclidean area fractions when its
Jacobian varies. Do not infer area invariance from coordinate cancellation.

### A tractable local twist

For v=x-c and a continuously differentiable scalar function phi of squared
radius, define

\[
F_c(x)=c+R_{\phi(\|v\|^2)}v.
\]

Radius is unchanged. Its inverse rotates by minus phi of the same squared
radius. In polar coordinates (r,theta) maps to (r,theta+phi(r^2)); the area
element r dr dtheta is unchanged, so det DF=1. This gives a globally one-to-one,
area-preserving family. A compactly supported example is
phi(r^2)=alpha(1-r^2/R0^2)^2 for r<R0 and zero outside; it joins with continuous
first derivative at R0.

Apply one continuous invertible map to the whole layer. Adjacent cells then
remain a tiling with shared boundaries; independently rotating isolated cells
would not provide that property. Cells may become curved in world coordinates.

For sample membership, apply the target layer's explicit inverse, then the
standard hex rounder. An area-preserving source deformation also preserves the
equal-area interpretation of transported source samples. Sampling error still
needs evaluation; the existing convex-polygon oracle does not automatically
become a curved-cell exact-area oracle.

Applying the same such twist to all layers preserves overlap fractions.
Twisting only one layer changes relative coverage and can reorganize native
relationships. This is a candidate mathematical family, not a capability
already present in the fixed Q40 production kernel. Its eventual deterministic
numeric representation and error treatment remain implementation work.

## 5. Fast motion evaluation from geometric boundaries

For the current 96-point stencil, let p_j be an integer Q40 point and k_j its
existing target. Use the six axial normals

\[
\mathcal H=\{(2,1),(1,2),(-1,1),(-2,-1),(-1,-2),(1,-1)\}.
\]

Precompute directional margins

\[
\sigma_{j,h}=S_0-h\cdot(p_j-S_0k_j),\qquad
m_h=\min_j\sigma_{j,h}.
\]

For a common translation delta, if h·delta<m_h for all six h, every sample
stays strictly inside its existing target. All target counts and Q16 weights
are therefore unchanged. This is a sufficient condition, not a necessary
description of every displacement with the same aggregate footprint.

At equality or possible crossings, reuse the original half-even/cube-repair
rounder for affected samples and the existing normalization. Preserve the
current 2*S0 even-anchor phase decomposition; odd translations are not an
unconditional parity symmetry.

Along delta=t v, the first possible boundary event occurs at

\[
t_* = \min_{h\cdot v>0}m_h/(h\cdot v).
\]

Thus candidate motion can skip intervals with identical sampled coverage.
Check both sides of an event as well as the actual tie rule. This uses the
event-driven idea of kinetic data structures, without introducing semantic
edges or persistent object-to-object routing.

For small affine changes delta_c+delta_A u, a conservative directional bound
comes from maximizing h·delta_c+h·delta_A u on the source hexagon's six vertices.
Six directions require at most 36 vertex evaluations. If independently
rounding the old and new coordinates to Q40, include the coordinate-rounding
error in the bound. Nonlinear twists require a valid displacement bound or
direct per-point inverse evaluation; the six-translation test is not universal.

### Deciding whether motion is useful

Pressure gives magnitude, not direction. Mirrored support layouts can have
identical pressure and opposite useful moves. The Host chooses semantic goals;
Core evaluates native geometric candidates.

For fixed material, compare the affected region before and after a candidate,
using the union of both influence regions. A useful diagnostic is total deficit

\[
G(R)=\sum_{c\in R}[D(c)-S(c)]_+.
\]

Moving eight unsupported units from one cell into two cells changes the maximum
illustrative pressure from 89 to 80, while G remains eight. It creates no lower
material. Conversely, balancing two still-deficient cells can improve the
pressure distribution while G stays unchanged. Therefore report total deficit,
the local pressure distribution, affected coverage and motion cost together;
G alone must not veto all moves or decide semantic usefulness.

This fixed-material relocation diagnostic does not require every new lower
write to reduce a sum over all layers. Such a requirement would recreate
unbounded pressure propagation.

The 96-sample weights are piecewise constant in motion, even before the final
1–100 score is rounded. Ordinary gradients of that score do not reliably find
useful motion. Boundary events provide candidate changes; they do not prove a
global optimum. Real-area weights can vary between sample events, so a future
real-area objective needs its own search/error treatment.

## 6. Actual exploratory evidence

These are local mathematical/kernel probes, not product integration or
semantic-memory quality tests.

- Exact Fraction comparisons on D,S in {0,1/4,...,20}: 52,488 monotonicity checks
  across the proposed deficit formula and a ratio comparator; no discrepancy.
  The deficit formula was preferred because fully supplied demand reaches its
  minimum rather than retaining nearly midpoint pressure.
- A fixed seed (20261122) generated 128 addresses, including large signed
  addresses; both directional kernels plus 12 deliberate tie/parity footprints
  gave 268 footprints. Twelve Q40 translations per footprint gave 3,216 cases.
  Selective recomputation and full 96-point recomputation had identical targets,
  counts and Q16 outputs in every case.
- In 1,608 small-translation cases, 1,570 reused the whole footprint. The
  remaining cases required 38 original nearest-cell calls against 154,368 in
  full recomputation. Call counts alone are not elapsed-time speedups.
- The inverse-up candidate widths above were computed with exact Fraction
  extrema and independently recomputed by the main reviewer. The omission
  witness was read against the unchanged actual coverage functions.

Local Python microbenchmark, median of five rounds, including crossing-point
updates, margin refresh and new target/cache materialization; fixed stencil
compilation is shared/excluded. Each query starts from the same base footprint,
so this measures reusable candidate evaluation, not an arbitrary motion history.

| Candidate set | Queries | Full recomputation | Incremental including maintenance |
|---|---:|---:|---:|
| All displacements | 3,216 | 500.0 ms | 396.5 ms |
| Small displacements, axial components <=1e-4 | 1,608 | 251.5 ms | 6.38 ms |
| Medium displacements | 536 | 82.5 ms | 46.9 ms |
| Large displacements | 1,072 | 167.7 ms | 321.7 ms |

Initializing all 268 footprints cost 53.3 ms for the baseline and 106.0 ms with
margins. Including initialization, the small-displacement batch improved about
2.71x; its reuse phase improved about 39.39x. The full batch improved about
1.10x including initialization. Large jumps were slower with incremental
maintenance. Use small-step reuse and full rebuilding when a large change
makes maintenance unhelpful; these are local observations, not universal or
end-to-end product speed claims.

No pytest suite or Provider Live acceptance was run for this documentation
review. Temporary generated probe logs are not production assets.

## 7. Concrete implementation implications

The immediate research interface is a local candidate-write report containing
the physical address/layer, after-write D, observed S and completeness, and the
advisory pressure. Keep this score separate from native coverage weights.

Current Access semantic writing is restricted to L0. A real pressure trial
needs an explicitly chosen multi-layer experimental writing path; merely
printing lower-layer scores would not implement the mechanism. The current
fixed 22.5-degree/scale profile similarly does not expose dynamic layer frames.

Future variable geometry needs a persisted physical-map representation and
queries against a consistent geometry state. Disposable caches must include
the relevant relative transform or geometry revision; existing address/direction
keys assume fixed transforms. Cache deletion must not change relationships.

For the requested experiment, material and physical geometry are authoritative;
coverage and motion margins are derived. Compare fixed geometry, advisory
pressure, and candidate deformation on meaningful evidence-backed writes and
later recall. Use an experimental field where bridge-assisted recall does not
explain an apparent improvement. Do not silently reinterpret an existing field
under a new geometry contract.

## Sources and provenance

- User's direct Nollm Project instruction, 2026-11-22: lower-layer support,
  advisory 1–100 pressure, broader deformation/anchor research, native coverage
  rather than graph/vector-style bridges.
- Inspected source at the fixed commit above:
  `packages/nollm-core/src/nollm_core/approximate_coverage.py`,
  `geometry.py`, `state.py`, `recall.py`;
  `packages/nollm-access/src/nollm_access/write_policy.py`;
  `reference/python/nollm/dream_geometry/geometry/types.py`, `chart.py`,
  `transform.py`, `coverage.py`.
- Historical `reference/python/nollm/cluster_pressure.py` and
  `protocol/CLUSTER_PRESSURE.md` describe a different diagnostic; they do not
  implement this support-deficit mechanism.
- Basch et al., [Kinetic Data Structures: Animating Proofs Through Time](https://graphics.stanford.edu/~comba/papers/socg.pdf):
  event-driven maintenance of continuous geometry's discrete structure.
- [CGAL Kinetic Data Structures manual](https://doc.cgal.org/Manual/3.7-beta1/doc_html/cgal_manual/Kinetic_data_structures/Chapter_main.html):
  predicate changes as relevant events.
- [ESMF regridding documentation](https://earthsystemmodeling.org/regrid/):
  conservative overlap-based transfer as background. Its intensive-value
  destination normalization is not the source-share count formula proposed here.

The pressure formula, inverse-up bound, six-margin specialization and selected
twist application are the present review's derivations/proposals. Their scope
and the finite verification results are stated above.
