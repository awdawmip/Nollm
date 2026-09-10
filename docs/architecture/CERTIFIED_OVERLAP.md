# Ideal hex overlap enclosures — Lab capability

Date: 2026-09-10. Owner: LAB. Status: IMPLEMENTED; admission evidence belongs to
the exact PR/run. This extends the merged phase-kernel baseline (`Nollm#4`,
`e798a72`) without changing its production approximation or stored-state identity.

## Scope and actual reuse

`certified_overlap.py` computes **source-area share intervals** for a supplied
physical address and one adjacent layer. It uses the existing Decimal oracle's
unwrapped relative axial chart convention: finer layers rotate by +22.5 degrees
and shrink by beta=2^(1/4). It does not resolve a different absolute/modulo-60
coordinate-label convention, introduce a new chart or change any stored address.

The existing `broad_residue.broad_exact_fixtures` and `oracle_decimal.coverage`
are executed unchanged by `run_certified_coverage_validation.py`. The production
Q40 phase kernel is consumed unchanged through its public expansion API.
The old Decimal calculation is a numerical cross-check, not a rigorous oracle.
No existing BRC arithmetic extractor is an area-intersection routine: those
implementations are NOT_APPLICABLE here. The admitted counted-phase interface is
COMPOSE_APPLIED: retain target identity and integer weights before the nonlinear
absolute-difference observer. Never collapse to total mass and call that error.

The retained carrier is `(target q,r, lower share, upper share)` for **every**
possibly positive-area target. Allowed later observations are partition mass,
support classification and distance to a supplied normalized Q16 distribution.
An absent sampled target is not assumed absent geometrically. The source address
and transform precision remain available for absolute-coordinate verification.
No user, statement, session, query, semantic score or persistent relationship
index is involved. This is Nollm Lab work, not an EM theorem-admission claim.

## Enclosure derivation

In source axial coordinates the centered hexagon is

```
H = {x : |2*xq+xr|<=1, |xq+2*xr|<=1, |xq-xr|<=1}.
area(H)=1, |xq|<=2/3, |xr|<=2/3.
```

Let B=[[sqrt(3),sqrt(3)/2],[0,3/2]], c=sqrt(2+sqrt(2))/2,
s=sqrt(2-sqrt(2))/2, t=s/sqrt(3). The ideal maps are

```
Tdown = beta * [[c+t,2*t],[-2*t,c-t]]
Tup   = 1/beta * [[c-t,-2*t],[2*t,c+t]].
```

All radicals are enclosed by integer square roots on a dyadic grid. Addition
is exact; multiplication/division round lower endpoints down and upper endpoints
up. Square roots use floor_isqrt(lo*2^p) and ceil_isqrt(hi*2^p). No floating pi,
trigonometry, guessed epsilon, Q40 matrix or sampled area defines the enclosure.

For source n and target k, the source-local overlap is H intersect the six
inequalities

```
h*T*x <= 1+h*k-h*T*n.
```

For each normal, let a,b be midpoints of interval-enclosed coefficients h*T,
d the midpoint of h*T*n, and ra,rb,rd their interval radii. For every x in H,

```
|h*T*x+h*T*n - (a*xq+b*xr+d)| <= E = rd+(2/3)*(ra+rb).
```

Thus clipping H by each nominal right-hand side minus E gives an inner region;
clipping with plus E gives an outer region. Rational line intersection and the
shoelace formula give exact rational inner/outer areas. The true source share is
between them. Parallel/boundary-only cases are handled without epsilon: a crossing
classification guarantees a nonzero interpolation denominator.

Candidate completeness is not inferred from sample hits or a guessed disk.
For row i of T, every point of T*H has coordinate magnitude at most
`(2/3)*(maxabs(T_i0)+maxabs(T_i1))`. A target center sharing a point with it is
within a further 2/3. Enumerating the exact integer rectangle obtained from these
bounds and the interval-enclosed T*n includes every positive-area target.
The candidate cap **raises**, never truncates. Targets outside the production
storage domain are retained in this mathematical calculation; production boundary
rejection is separately reported by the runner.

A zero upper area certifies no positive-area overlap. A positive lower area
certifies overlap. Lower=0<upper remains unresolved, even when extremely small.
The partition check requires `sum(lower)<=1<=sum(upper)` and does not renormalize
or manufacture a residual target to force that identity.

## Bounded refinement and error readout

`certify_coverage` increases dyadic precision within an explicit finite budget.
Default target: sum of source-share interval widths <=2^-64; max precision 192
bits. This tolerance describes the **oracle**, not the 96-sample production
kernel. Exhaustion raises `CertificationBudgetExceeded`, never a fabricated pass.

For exact Q16 value w and interval [l,u],

```
max(0,l-w,w-u) <= |true_share-w| <= max(|w-l|,|w-u|).
```

Summing per-target bounds and dividing by two encloses total variation. Summing
shares for zero-weight targets encloses missed mass. Target identity must survive
until after absolute values. The existing Q16 normalization only proves its
weights sum to 65536; it says nothing about these physical approximation errors.

The runner reuses the frozen broad fixture generator (128 samples per phase and
direction =2048 requests) and reports exact outward-rounded dyadic bounds, numeric
cross-check discrepancies, missed positive targets, precision use, and explicit
production storage failures. Its 1/20 error bucket is a diagnostic threshold, not
a new product invariant. Finite-population maxima are not whole-domain bounds.

## Tests and admission

The standalone tests check directed arithmetic using rational endpoints; exact
hex areas and degenerate clips; analytic origin values; coordinate sign symmetry;
layer covariance; inverse transform and eight-step interval witnesses; reciprocal
source-area scaling; target-preserving error readout; invalid inputs; candidate
and precision budgets. The analytic identity Tdown^8=-4I follows from B conjugacy,
beta^8=4 and R(-pi)=-I; its numerical interval test is not permission to apply this
identity to repeated rounded production steps.

Run on a normal repository environment:

```
python -m pytest -q lab/nollm-lab/geometry/tests/test_certified_overlap.py
python lab/nollm-lab/geometry/run_certified_coverage_validation.py --output <external-path>/coverage.json
```

The runner requires the normal public Core import path. All generated evidence
stays outside the active Git tree. Existing Core/Access/Snapshot/Trace/Formation
and governance gates remain required; no test or product contract is relaxed.

## Not delivered by this capability

This is not a production replacement, a full phase-region atlas, a theorem about
uniform 96-sample error, proof of exact support on every boundary, a new chart
migration, a memory-quality benchmark, or Windows/OpenClaw Provider Live approval.
The implementation and containment argument have executable tests, not a formal
proof-assistant verification. Before any production switch: compile a bounded
integer evaluator, preserve uncertainty and mass semantics, establish independent
geometry/quantization gates, and explicitly version migration when outputs change.
