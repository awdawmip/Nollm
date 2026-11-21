# Nollm develops from its own memory

This is the executable continuation of [PR #7](https://github.com/awdawmip/Nollm/pull/7)
and the [self-bootstrap plan](../../../../docs/project/tasks/NOLLM_SELF_BOOTSTRAP_DEVELOPMENT_PLAN_20261121.md).
The source baseline is `d25083d062c86a7b903d53348ddb1bdf23f24bda` (2026-11-21).

## Open the accepted field

From a Nollm checkout:

```sh
python lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field lab/nollm-lab/repository_memory/self_bootstrap/field walk
```

Choose the candidate IDs actually shown on each page. A selected physical entry
returns its bounded neighborhood. `--cursor-file /path/to/walk.json` resumes a
walk without replaying all choices; omit choices when starting a new cursor.
`--steps`, `--limit`, and `--via local|vertical|connected` control native expansion.
The Host chooses semantics and the final physical entry; Core executes geometry.

Use the same command prefix with `show ID` to open an exact expression and with
`source --id ID --number N --repo /path/to/Nollm` to read its fixed Git source.
The source repository must contain the cited commit. `find TERM` is a separate
literal helper, not the native discovery path.

Keep a working field outside an installed runtime directory. Pass its path
explicitly after replacing or reinstalling the runtime. `project` requires a
field; `save` and `source` additionally require the corresponding source repo.
The `em` wrapper retains its existing supplied field and uses the same code.

## Seed M0

The initial M0 field contains fourteen independent cross-file judgments,
fourteen L0 occupied cells, and one directed Stitch. The formation model read
the actual source and chose positions by meaning. Forty-seven distinct fixed
source windows were expanded through the existing source reader.

The statements cover evidence/semantics/geometry, rotated overlapping Coverage,
Surface observation, bounded recall, navigation state, cell-level Stitch,
kernel identity, Core persistence, Statement versions, current/supporting
bindings, Git sources, the project adapter, and installation lifetime.

Related conditions live in neighboring cells. The directed installation-to-Core
connection records that a replacement runtime must interpret the accumulated
field. Its reason is written in the statement as well; coordinates and Bridge
weights do not prove a dependency. All expressions are stored on L0 while native
upper/lower Coverage remains available during recall.

M0 is an implementation snapshot, not a claim that its source facts remain true
after every patch. Maintenance preserves exact old expressions and revises the
affected current slots from real code changes. `current` describes field binding;
the cited commit describes the code supporting that expression.

## Runtime measurement

The small diagnostic profiles one field reopen and reads each current statement;
it then reports unprofiled repeated-process-lifetime timings:

```sh
python lab/nollm-lab/repository_memory/self_bootstrap/measure_runtime.py \
  --runtime /path/to/Nollm --field /path/to/accepted-field
```

It reports actual decoder/encoder calls and local wall time. These are runtime
observations, separate from model formation, navigation, development and maintenance
costs. The full model token usage and billed cost are not exposed by this environment.

## Development evidence

A new-context developer used M0 through Surface, selected one physical entry,
read the neighboring persistence/registry/Statement/binding judgments, and opened
the fixed source windows before editing Core/Access. The source tree also gained
a shared project adapter and installed `project` command in a separate integration
workstream. The developer then used that integrated entry on an M0 copy.

C1 removes repeated Core decoding, read-time JSON re-encoding in the Statement
and binding stores, and per-construction fixed-template SHA self-checks. Packaged
templates and their existing persistent geometry identity are reused per process.
Core and binding imports accept equivalent JSON presentation and write canonical
output. Unique bindings, original Statement identity, geometry, file replacement,
resource ownership and rollback retain their actual behavior.

Initial related Core/Access/Snapshot tests: 109 passed. After the observed binding
encoder overhead was included, 28 affected tests passed; the three project/skill
installation tests passed again. These counts overlap. Five project/EM/skill
installation tests had passed before the binding increment. The actual M0-copy
exercise reopened 14 statements, saved and revised a new statement, preserved
historical source text, followed and removed the existing directed link, and
restored the Core snapshot. A new test initially used the wrong chart name for
`default_dream_v1`; the fixture was corrected. Pytest was installed after the
first invocation reported that the runner was absent.

On the same unchanged M0, the initial reopen had 2 Core decodes, 4 Core canonical
encodes, 14 Statement canonical encodes, and 2 binding canonical encodes. C1 had
1 Core decode and no read-time encodes in these stores. Thirty unprofiled
same-process reopen-and-read repetitions had medians 6.620 ms (C0) and 1.120 ms
(C1). This is a small local runtime measurement; fresh-process startup, model
work and total development cost are separate.

The C1 developer accidentally saw the completed project-adapter agent's short
status through the agent-list tool. It contained that independently integrated
entry's changed paths and tests, not the Core patch. The session otherwise started
without the formation conversation. This development exercise is not a strictly
isolated blind comparison.

## Maintained M1 and C2 checkpoint

C1 is fixed at `e0e0dd80039d129b7a0321e1e640ffa0c987f9eb`. The field shipped at this
checkpoint is M1: eight in-place revisions from C1, six retained judgments,
fourteen current judgments, and twenty-two readable versions. All old texts and
sources, physical positions and the directed bridge were retained. Thirty-seven
new fixed C1 source windows were expanded. The original M0 remains in C1 history.

A second fresh Native developer used M1 and completed the [C2 task](C2_TASK.md):
project `save --reuse CURRENT_ID`, supporting expressions with their own fixed
sources, exact current-version display, and later revision with historical
readback. It chose physical entry `L0(1,-1)` from Surface, received five judgments,
and expanded the binding judgment's fixed Access/adapter sources. The accepted
implementation also rejects a supporting ID used as a current revision/reuse
target. Core/Access geometry and storage formats are unchanged.

The clean Native submission passed four installed/API behavior tests, nineteen
related Access regressions and the independent end-to-end behavior check. The
integrator added an assertion for the observed supporting-ID revision error;
both project tests passed. Source and Flat submissions plus an initial Native
run are retained in the development evidence. Subsequent review found the
supporting-ID target error in Flat and initial Native. A malformed shell command
in initial Native generated out-of-scope material; a separate clean Native
session was run, preserving the original attempt and its costs. No Native
quality or total-cost advantage is established by this one-task comparison.

M2 maintenance will cite this C2 code commit and use the new supporting-expression
operation in the actual self-bootstrap field. This checkpoint preserves M1 as
used by the second development comparison.

Raw tool transcripts, measured outputs and intermediate field copies are kept
outside the source tree. This directory retains the accepted usable field,
reproduction code, and the concise continuation record.
