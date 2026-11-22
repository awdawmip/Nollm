# C3/M3: native encounters and bounded recall

Observed 2026-11-21. This continues the [self-bootstrap record](README.md) and
[PR #7](https://github.com/awdawmip/Nollm/pull/7). The code correction is fixed at
[`a1c0f5a74434fd5e3a5429b794366a3d2739aadf`](https://github.com/awdawmip/Nollm/commit/a1c0f5a74434fd5e3a5429b794366a3d2739aadf)
(C3), based on `260faeadb796d8057c9ddbfc5c2a5cc51f06037f`.
The implementation was published on the existing task branch and its 24 changed
blobs read back at that fixed commit. Field maintenance and this report follow
the code publication; their source references use C3, not uncommitted prose.

The delivered behavior is a native-default project-memory workflow: Host observes
Surface, chooses one physical entry, reads a bounded locality, then decides
recall, reuse, revision, new placement, none or defer. Source navigation and
heuristic comparison remain explicit tools. Core also stops spending beam slots
on revisits that will be discarded and reports clipping consistently.

The evidence has three distinct scopes: focused behavior tests, a controlled
old/new propagation comparison on unchanged M2, and a fresh Host's actual use
of the installed encounter. The fixed mixed-kernel beam-16 miss remains visible.
The [compact run evidence](architecture_correction_evidence.json) preserves
comparison IDs/budgets, reader results and command summaries including failures,
and M3 maintenance outcomes and source-window checks.

## 1. Fixed inputs and maintained state

| Object | Exact basis and role |
| --- | --- |
| Previous code and M2 | `260faeadb796d8057c9ddbfc5c2a5cc51f06037f`; fourteen current judgments, twenty-five readable expression versions, fourteen occupied L0 cells, one directed bridge. |
| C3 runtime | `a1c0f5a74434fd5e3a5429b794366a3d2739aadf`; native encounter and bounded-recall correction. |
| Propagation comparison | The same frozen M2, the same explicit physical entry and budgets, under the previous and corrected implementations. No memory formation, layout change or bridge was used to improve an answer. |
| Fresh Host | Installed corrected runtime plus its own M2 copy. It checked source at `260faeadb796d8057c9ddbfc5c2a5cc51f06037f`; those source facts are distinct from the executing runtime version. |
| Accepted M3 | Four in-place revisions against fixed C3 source; fourteen current judgments, twenty-nine readable versions, fourteen occupied L0 cells/atoms, one bridge. All twenty-five earlier expression files, ten unaffected bindings, positions and the bridge were preserved. |

The fresh Host's added expression belongs to its separate field copy. Its fifteen
facts are not the accepted M3 count and are not merged into the accepted field.
Historical C1/C2 tasks, Source/Flat/Native runs, failed collection and source
assistance remain in the [earlier record](README.md).

## 2. Native entry and explicit auxiliary routes

The [skill][skill] and [dispatcher][dispatcher] now lead ordinary repository work
to `project --field FIELD encounter --cursor-file SESSION`; `em encounter` shares
that interface with the research field's existing default. The Host authors
meaningful statements, reads their evidence and makes the semantic choice.
The program does not score task words, follow a source-to-cell table or select
the entry from a source graph on this path.

The [project adapter][adapter] retains current/supported/historical expression
semantics. Reuse saves a distinct supporting expression with its own ID and
sources while retaining the existing current judgment and occupancy. Revision
replaces the current judgment in place and preserves old expressions. New
placement can use a displayed occupied cell for a distinct proposition, or a
vacant candidate supplied by Core's geometric Junction solver. A new empty field
first presents the origin as a physical candidate for the Host to choose.

The encounter cursor holds disposable navigation and locality parameters. It
retains one entry while the Host explicitly changes propagation budgets, and is
removed after a terminal CLI outcome. Existing `walk`, exact `show/source`, and
direct `save` remain available. An exhausted or unhelpful locality does not
silently invoke a lexical baseline.

### Command migration

| Earlier unqualified command | Explicit command | Actual role |
| --- | --- | --- |
| `brief`, `source`, `inventory`, `capture`, `review`, `status`, `view` | `aux` followed by the earlier command | Git evidence manifests and source inspection. |
| `facts`, `records`, `route`, `check-marks` | `aux` followed by the earlier command | Static source facts, explicit relations and source-navigation candidates. |
| `coverage` | `aux coverage` | Explicit-position Coverage experiments. |
| `geometry` | `aux aoci` | Reversible AOCI encoding and inspection. |
| `geometry-native` | `aux aoci-field` | Native representation of supplied AOCI slots and explicit references. |
| `recall` | `baseline recall` | Lexical entry scoring with shared-source heuristic layout. |
| `field` | `baseline field` | Source/graph-routed entry selection and heuristic layout. |

Unqualified legacy commands return a migration message. Their comparison
outputs identify `lexical_source_layout_baseline` or
`source_routed_<layout>_baseline`; newly built heuristic fields record fixture
placement provenance. Historical files keep their historical meaning.
The [auxiliary reference][auxiliary] documents these opt-in workflows.

## 3. Bounded recall correction and fixed-M2 result

The previous loop sorted merged targets and applied `beam` before discarding
non-improving revisits. A high-ranked return to an already visited cell could
consume a slot and then be thrown away, even though a new cell was available
below the cutoff. [C3 recall][recall] removes those revisits before beam selection,
while retaining a revisit whose score or deterministic path ordering improves.
It also reports beam and result-limit clipping, and avoids declaring exhaustion
merely because terminal targets are revisits or outside the permitted layer span.

The fixed comparison used entry **L0(0,1)**, two propagation steps, layer delta
two, lateral ring one, no bridge steps and a result limit of twenty. The field
was M2 in both runs. The table reports returned current judgments.

| Kernels | Beam | Previous runtime | C3 | Observed change |
| --- | ---: | ---: | ---: | --- |
| Coverage up/down plus lateral | 16 | 4 | 4 | The original mixed-budget miss remains. |
| Lateral only | 16 | 8 | 9 | One additional judgment returned. |
| Coverage up/down only | 16 | 3 | 4 | One additional judgment returned. |
| Coverage up/down plus lateral | 64 | 9 | 9 | Same returned count. |
| Coverage up/down only | 64 | 7 | 7 | Same returned count. |

In the corrected mixed-kernel case, the needed binding cell ranked **38** among
eligible candidates. Removing discarded revisits therefore does not bring it
within beam 16. This result supports the specific revisit repair and the observed
small-budget gains; it does not support claiming the original mixed-16 binding
miss is fixed or increasing every caller's default budget. Coverage targets,
weights, physical layout and persistent geometry identity were unchanged.

The committed [compare_recall.py][comparison] emits the entry, exact budgets,
returned IDs, native paths, scores and exhaustion status. Run it once with each
runtime against the same preserved M2 field:

```sh
python lab/nollm-lab/repository_memory/self_bootstrap/compare_recall.py \
  --field /path/to/frozen-M2 --runtime /path/to/previous-skill/scripts/runtime
python lab/nollm-lab/repository_memory/self_bootstrap/compare_recall.py \
  --field /path/to/frozen-M2 --runtime /path/to/C3-skill/scripts/runtime
```

Omitting `--runtime` selects the checkout's Core and Access. Obtain frozen M2
from `260faeadb796d8057c9ddbfc5c2a5cc51f06037f`; the evolving accepted field is a
different input. This script supplies a controlled geometric entry, so its counts
measure propagation rather than a model's ability to discover or use the entry.

## 4. Fresh Host used the installed common encounter

A separate model session read the installed skill and used its own M2 copy to
answer what must survive runtime replacement and what understanding should change
with code. The [compact evidence](architecture_correction_evidence.json) retains
its result and actual command summaries, including failed attempts. The full
command log, answer and authored statement were also retained in the run workspace;
their local paths are not presented as portable repository links.

The executing dispatcher, project adapter and Core recall files were compared
byte-for-byte with C3 and matched. The skill descriptor read by this Host preceded
two final clarifying sentences: previews can be excerpts, and budget changes are
observed before a separate terminal call. The evidence includes that exact text
diff. The Host already used separate observation and decision calls; the final
descriptor was not subjected to a second fresh-Host run.

The log records three Surface pages, then a physical-candidate page, for
`surface_calls=4`. The Host selected **L0(0,0)**. It did not change the entry as it
expanded the locality:

| Steps / beam / result limit | Returned | What the Host obtained | Exhausted |
| --- | ---: | --- | --- |
| 1 / 16 / 5 | 5 | Core reading, Stitch, recall, registry and Statement storage; binding was absent. | true |
| 2 / 32 / 16 | 9 | Added the current binding judgment and nearby commit/navigation context. | true |
| 4 / 64 / 20 | 11 | Added the fixed-source judgment and architecture context; returned paths included actual Coverage transitions. | true |

These are three observations of the same entry, not three independent entry
selections. The later Coverage paths show that those native operators executed;
this task did not compare their benefit against an aligned alternative.

The Host expanded fixed code windows at `260faeadb796d8057c9ddbfc5c2a5cc51f06037f`
and formed a cross-file judgment: replacing runtime code should retain the full
working field and access to cited Git revisions; a SnapshotService using CoreRuntime
alone exports Core state and does not contain Access's separate bindings and
Statement files. It inspected current `nollm.binding.v3`, historical
`nollm.binding.v2`, and supporting `nollm.binding.installed-support.v1` with their
distinct current flags and sources.

The supporting expression's ID came from an **explicit auxiliary read of
`access/bindings.json`**, followed by exact CLI `show/source`. That support-ID
discovery is not credited to native recall. Two source requests exceeded the
files' actual length: Statement store L1–L140 for a 110-line file, and Snapshot
service L1–L35 for a 27-line file. Both failed visibly and were corrected to the
actual windows; the failed commands and outputs remain in the log.

In the same encounter, the Host chose displayed `cell:0:1:1` and saved
`nollm.runtime-field-continuity.v1` with six pinned source windows. The result
reported `effect=new`, original entry `[0,0,0]`, and placement `[0,1,1]`.
Independent CLI processes then read back its full body, `current=true`, and the
fifth fixed source. Atom and binding counts rose from fourteen to fifteen, the
original support and `installation-reopens-state` bridge remained, and the terminal
cursor was deleted. The Host did not run a test suite or install a second runtime;
it read the existing committed replacement test and exercised the supplied
installed runtime's actual navigation, source, write and reopen path.

### Use the same interface

Use the actual installed CLI, persistent field and corresponding source repository.
Each independent shell invocation should set these variables again, or use the
absolute paths directly.

```sh
cli='/absolute/path/to/nollm-repository-memory/scripts/memory.py'
field='/absolute/path/to/persistent-project-field'
repo='/absolute/path/to/Nollm'
session='/tmp/nollm-encounter.json'
python "$cli" project --field "$field" encounter --cursor-file "$session"
```

Set `candidate_id` to an ID actually shown, and pass successive choices with the
same cursor. Use `next` when another page is needed. Once `kind=locality` appears,
the Host can inspect the returned expressions and explicitly reopen that entry
with a larger budget, as this reader did:

```sh
python "$cli" project --field "$field" encounter "$candidate_id" --cursor-file "$session"
python "$cli" project --field "$field" encounter --cursor-file "$session" \
  --steps 2 --beam 32 --limit 16
```

For a query, choose `--recall "$fact_id"`, `--none` or `--defer`. For an incoming
proposition, choose a shown cell or current fact and provide a new expression ID,
body and sources. This is the terminal command shape used by the fresh Host,
with paths and the selected cell supplied by that encounter:

```sh
python "$cli" project --field "$field" encounter --cursor-file "$session" \
  --new "$cell_id" --id nollm.runtime-field-continuity.v1 \
  --repo "$repo" --rev 260faeadb796d8057c9ddbfc5c2a5cc51f06037f \
  --cite 'packages/nollm-core/src/nollm_core/state.py#L93-L117' \
  --cite 'packages/nollm-core/src/nollm_core/state.py#L442-L465' \
  --cite 'packages/nollm-access/src/nollm_access/handle_store.py#L43-L84' \
  --cite 'packages/nollm-access/src/nollm_access/statement_store.py#L20-L65' \
  --cite 'packages/nollm-snapshot/src/nollm_snapshot/service.py#L7-L24' \
  --cite 'lab/nollm-lab/repository_memory/test_project_memory.py#L98-L117' \
  < understanding.txt
python "$cli" project --field "$field" show nollm.runtime-field-continuity.v1
python "$cli" project --field "$field" source \
  --id nollm.runtime-field-continuity.v1 --number 5 --repo "$repo"
```

For another task use its actual source windows, Host-authored body and a fresh
immutable ID. Reuse/revision select `--reuse "$fact_id"` or `--revise "$fact_id"`
instead of `--new`; they still use the same observed locality and entry.

## 5. Focused verification and independent review

| Verification group | Actual result | Scope |
| --- | --- | --- |
| Installed skill, explicit older tools and repository compatibility | 20 passed, 12 subtests; 14.87 s | Portable installation, native path independent of legacy retrievers, explicit command migration and retained auxiliary/baseline behavior. One third-party pytest deprecation warning. |
| Encounter and existing project/EM interfaces | 7 passed; 49.433 s | Common navigation, same-cell distinct propositions, support/current/history semantics, budget changes, exact sources and separate-process CLI use. |
| Core recall, exact geometry and canonical recall contract | 9 passed; 0.09 s | Revisit filtering, improving revisits, beam/result clipping and existing geometric/ordering contracts. |
| Same Core test set with the previous recall function | 4 failed, 5 passed | Four of the changed-behavior failures reproduced against the baseline implementation. |
| Independent targeted review run | 10 passed, 6 subtests; 0.51 s | Overlaps the preceding groups; independently checked recall, encounter persistence/locality and legacy command messages. |

The test counts overlap and are not added into a total sample count. Independent
source review found no actionable regression in the reviewed correction;
`git diff --check` passed. The new [encounter tests][encounter-tests],
[recall tests][recall-tests] and [installed tests][installed-tests] preserve the
relevant behavior. These runs were selected for the changed paths; no full
historical matrix was rerun.

The reported commands were:

```sh
# From the repository root.
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src:lab/nollm-lab/repository_memory \
python3 -m pytest -q \
  lab/nollm-lab/repository_memory/test_skill_install.py \
  lab/nollm-lab/repository_memory/test_machine_install.py \
  lab/nollm-lab/repository_memory/test_geometry_install.py \
  lab/nollm-lab/repository_memory/test_coverage_install.py \
  lab/nollm-lab/repository_memory/test_task_recall.py \
  lab/nollm-lab/repository_memory/test_repository_memory.py

# From lab/nollm-lab/repository_memory.
PYTHONPATH=../../../packages/nollm-core/src:../../../packages/nollm-access/src \
python -m unittest -v \
  test_project_encounter test_project_memory test_enterprise_math_api test_enterprise_math

# From the repository root.
PYTHONPATH=packages/nollm-core/src python -m pytest -q \
  packages/nollm-core/tests/test_core_recall.py \
  packages/nollm-core/tests/test_core_recall_exact_geometry.py \
  packages/nollm-core/tests/test_canonical_recall_contract.py
```

## 6. M2 to M3 maintenance

The main task maintained the accepted field against fixed C3 source using the
newly installed CLI. Each revision began at Surface, selected one physical entry,
observed its locality and applied `--revise` to the current expression. The four
successful terminal outcomes were:

| M2 expression | M3 expression | Retained cell | Meaning affected by C3 |
| --- | --- | --- | --- |
| `nollm.recall.v1` | `nollm.recall.v2` | L0(-1,1) | Beam selection after revisit filtering and accurate clipping status; bounded reach still matters. |
| `nollm.navigation.v1` | `nollm.navigation.v2` | L0(-2,1) | Encounter previews, disposable state, one retained entry and explicit budget reopening. |
| `nollm.adapter.v3` | `nollm.adapter.v4` | L0(3,-1) | Shared query/proposition encounter, current-locality decisions and distinct propositions in an occupied cell. |
| `nollm.installation.v2` | `nollm.installation.v3` | L0(4,-1) | Installed reference material, command migration and reuse of the persistent field. |

All new sources are pinned to `a1c0f5a74434fd5e3a5429b794366a3d2739aadf`.
Fourteen new source windows were individually expanded and read back. A separate
process verified fourteen current judgments, twenty-nine expression versions,
fourteen occupied physical cells, fourteen Core atoms and one native bridge.
It compared the pre-maintenance field and confirmed every one of its twenty-five
expression JSON files remained byte-for-byte unchanged, all ten unaffected
bindings remained equal, and the geometric positions and bridge were unchanged.
All four terminal cursor files were gone. The twenty-six logged maintenance
commands had no failed calls.

The [compact evidence](architecture_correction_evidence.json) records the four
terminal results and these checks. The fresh reader's independent fifteenth fact
remains in its own copy; it is not part of M3. Maintenance updated the four
affected meanings, without re-forming the field or retuning its layout.

## 7. Remaining work established by this run

The mixed-kernel beam-16 binding miss remains a concrete propagation/allocation
case. A subsequent development task can use the maintained M3 to investigate it
with the same frozen input, while retaining the distinction between reachable,
returned, read and correctly used evidence. The present repair changes no
semantic placement policy or Coverage weights.

Surface's existing [preview code][surface-navigation] limits each excerpt to
256 characters. The `truncated` flag reports omitted statements, so a clipped
single-statement excerpt can still have `truncated=false`; the fresh Host's log
contains such mid-sentence previews. The encounter preserves those Access
excerpts and supplies full bodies in locality. Clarifying the preview signal is
a small outstanding presentation issue, not a reason to restore heuristic entry
selection.

The fresh Host demonstrates an installed read/write/source cycle and preservation
of its copy's current/support/history state. Its execution used one runtime
installation. Replacement behavior has the focused existing test coverage above;
this Host run is not an independent second-install demonstration. The controlled
counts and one Host task establish the reported local behaviors. Comparative
memory quality, model cost and a specific Coverage advantage need an appropriately
aligned subsequent task; they are not inferred from these results.

[skill]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/skills/nollm-repository-memory/SKILL.md
[dispatcher]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py
[adapter]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/project_memory.py
[auxiliary]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/skills/nollm-repository-memory/references/auxiliary.md
[recall]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/packages/nollm-core/src/nollm_core/recall.py
[comparison]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/self_bootstrap/compare_recall.py
[encounter-tests]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/test_project_encounter.py
[recall-tests]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/packages/nollm-core/tests/test_core_recall.py
[installed-tests]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/lab/nollm-lab/repository_memory/test_skill_install.py
[surface-navigation]: https://github.com/awdawmip/Nollm/blob/a1c0f5a74434fd5e3a5429b794366a3d2739aadf/packages/nollm-access/src/nollm_access/surface_navigation.py
