# Nollm V2L0-C1：活动导航去 V1 化与交付证据闭合任务书

**日期**：2026-07-07  
**阶段**：V2L0-C1 — Active Navigation De-V1 Closure / Evidence Closure  
**前一候选代码头**：`5e3f9bd4547d2c6b0797b0f1ef82544be33aa7dc`  
**活动开发基线**：`8bb324a3a5de46bebb6eadd217820627a971e2a0`  
**已接受、未提升组件**：HAG1-C1R `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`  
**继续分支**：`codex/v2l0-layer-constitution-source-reclassification`  
**执行主体**：单一执行主体；禁止子代理、并行代理、后台执行。  
**交付**：一个 complete-history Git bundle + final-head parentless TQ1 evidence capsule。  
**本任务不做**：不删除或移动 V1 / MT1 / old prototype / OpenClaw source；不修改任何 sealed production module；不合并 HAG1-C1R；不 promotion main；不 push / pull / fetch。

---

## 0. 本轮唯一目标

V2L0 的分层宪法与 Core import firewall 方向正确，但当前 candidate 有三个交付阻断：

```text
1. README / ARCHITECTURE / ROADMAP 仍保留完整 V1 route-lock 与 V1 tool action appendix；
2. AGENTS 仍把 nollm.cli validate/audit examples/openclaw 列为 Required Validation Commands；
3. V2L0 taskbook 未提交进 code history，final evidence capsule 也未封入 raw V2L0 gate / V2 regression logs。
```

本轮唯一目标是闭合这些导航与证据缺口，使 repository root 的**唯一日常操作入口**为 V2 分层和 V2 validation，而 V1 只作为 `docs/history` 所指向的物理历史资产存在。

本轮不是 V1 physical deletion，不是 OpenClaw migration 实现，不是 HAG integration，也不是 Core contract revision。

---

## 1. Start conditions

开始前必须确认：

```powershell
git switch codex/v2l0-layer-constitution-source-reclassification
git status --short
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git merge-base --is-ancestor 5e3f9bd4547d2c6b0797b0f1ef82544be33aa7dc HEAD
```

开始条件：

```text
- current branch 必须为 codex/v2l0-layer-constitution-source-reclassification；
- 5e3f9bd... 必须是 current HEAD 的祖先；
- local main 必须精确为 8bb324a...；
- worktree clean；
- HAG branch 和 refs/nollm-delivery/tq1-c7r/0e0d21... 不得改写；
- 不新建 parallel C1 branch；
- 不 reset / rebase / squash / cherry-pick / merge；
- 不 fetch / pull / push。
```

若 local main 不是 `8bb324a...`，立即停止并报告 refs；不得从旧 bundle 的 remote-tracking ref 推断本机状态。

---

## 2. Sealed and forbidden

继续 sealed：

```text
DE1, DG1, DG2, DC1, DA1, DF1, DR1, DI1,
CI1, CX1, CX2, BA1, HX1, HCG1,
HAG1-C1R, TQ1-C7R。
```

绝对禁止：

```text
- 修改 reference/python/nollm/dream_geometry/**；
- 修改 HCG / HAG / HX1 / CX2 implementation 或其 tests；
- 修改 TQ1 runner、packager、verifier；
- 删除、移动或重命名任何 V1 / MT1 / OpenClaw / prototype source、tests、examples 或 scripts；
- 改 pyproject / package identity；
- 激活 OpenClaw runtime、network、daemon、database、cache、LLM、NLP、embedding 或 semantic search；
- 将 V1 compatibility import 加入 V2 Core；
- main promotion；
- remote operation；
- 子代理。
```

---

## 3. Allowed paths

仅允许修改或新增：

```text
README.md
ARCHITECTURE.md
ROADMAP.md
AGENTS.md

protocol/v2/LAYER_CONSTITUTION.md
protocol/v2/LEGACY_BOUNDARY.md

docs/architecture/NOLLM_PROJECT_BOOK_V2_2_LAYERED_CORE_TO_TERMINAL.md
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
docs/project/NOLLM_SOURCE_TOPOLOGY_V2.md
docs/history/V1_RETIREMENT_RECORD.md
docs/history/OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/delivery/V2L0_DELIVERY_REPORT.md
docs/delivery/NOLLM_V2L0_LAYER_CONSTITUTION_AND_SOURCE_RECLASSIFICATION_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1_ACTIVE_NAVIGATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md

reference/python/tests/test_v2l0_layer_constitution.py
reference/python/tests/test_v2l0_source_reclassification.py
reference/python/tests/test_architecture_language.py
reference/python/tests/test_terminology.py
reference/python/tests/test_repository_hygiene.py
reference/python/tests/test_package_hygiene_script.py
reference/python/tests/test_run_tests_runner.py
```

不得修改上述 allowlist 以外任何文件。若某旧 V1 test 或 script 的行为导致必须扩展 allowlist，停止报告，不得顺手扩大。

---

## 4. Root navigation closure

### 4.1 Root documents must not be V1 operation manuals

从下列 root docs **删除完整 V1 route-lock/action appendices**：

```text
README.md
ARCHITECTURE.md
ROADMAP.md
AGENTS.md
```

root docs 可以保留一句、并只保留一句清晰历史指针：

```text
V1 / MT1 / pre-V2 prototype source remains physically present as retired history;
see docs/history/ for classification and migration boundaries.
```

root docs 不得再包含：

```text
Nollm V1 Route Lock
Stable historical V1 tool actions
nollm.validate / nollm.orient / nollm.recall / nollm.read_card ...
nollm.cli
examples/openclaw
legacy V1 non-goal lists
完整 V1 Card/Anchor/ledger route explanation
```

这些内容若需保留，只能由 `docs/history/V1_RETIREMENT_RECORD.md` 简短指向 Git history；不得把 V1 操作表、命令表或可执行流程复制到活动 root navigation。

### 4.2 AGENTS commands must be V2-only for ordinary work

删除：

```powershell
python -m nollm.cli validate ../../examples/openclaw
python -m nollm.cli audit ../../examples/openclaw
```

`AGENTS.md` 中 ordinary repository validation 应只描述：

```text
- V2 component-local pytest gates；
- explicitly scoped CI1/CX1/HCG1/HX1 public regression gates；
- TQ1 final matrix / capsule / verify-ref for delivery-grade acceptance。
```

`python run_tests.py` 可以保留，但只可标注为：

```text
legacy-inclusive repository diagnostic;
not the primary V2 component acceptance gate;
not evidence that V1 is active architecture.
```

不得把 `run_tests.py` 或任何 legacy test 输出称为 V2 semantic acceptance 的唯一依据。

### 4.3 Required root-document assertions

root docs 必须明确：

```text
V2 is the only active architecture.
protocol/v2 is the only active protocol root.
V1 / MT1 / prototype are retired history.
OpenClaw is a frozen L5/L6 migration asset, not current runtime.
Core does not import adapters or terminals.
Adapters do not own facts.
Terminals do not bypass L4.
HCG is accepted L5 File Capture Adapter.
HAG1-C1R is accepted / unpromoted L5 File Admission Adapter;
V2L0-C1 does not merge or modify it.
```

---

## 5. Generic test migration — replace V1-current assertions with stronger V2.2 assertions

V2L0-C1 must not evade old generic tests by preserving V1 operation text. It must migrate their assertions while keeping quality coverage explicit.

### 5.1 `test_v2l0_layer_constitution.py`

Add a negative root-navigation test covering all four root docs:

```text
must not contain:
  "Nollm V1 Route Lock"
  "Stable historical V1 tool actions"
  "nollm.cli"
  "examples/openclaw"
```

Also assert every root doc contains:

```text
"V2 is the only active architecture"
"protocol/v2"
"L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0"
```

### 5.2 `test_v2l0_source_reclassification.py`

Strengthen source-classification assertions:

```text
- root docs do not list executable V1 tool actions;
- root docs do not use V1 CLI as Required Validation Commands;
- protocol/v2 is stated as the active protocol root;
- OpenClaw legacy is classified as migration asset, not current runtime;
- HCG/HAG are not claimed to register on V1 CLI/tool surface.
```

Do not merely check a narrow banned-phrase list; test the required replacement concepts.

### 5.3 `test_terminology.py`

Replace the V1-current expectation:

```text
examples/openclaw exists
```

with a V2.2 classification expectation:

```text
- `docs/history/OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md` exists;
- it states OpenClaw is frozen migration asset and not current runtime;
- `protocol/v2/LAYER_CONSTITUTION.md` identifies future OpenClaw adapter/terminal work as L5/L6;
- no obsolete alternate product namespace is introduced.
```

Retain prohibited-terminology detection quality; do not delete that coverage.

### 5.4 `test_repository_hygiene.py`

Replace hard requirements for V1 OpenClaw audit/recall sample fixtures with:

```text
- no generated artifacts in active tree;
- no machine-local absolute paths in committed fixtures;
- V2 source topology, V1 retirement record and OpenClaw migration record exist;
- README / PACKAGING distinguish `run_tests.py` diagnostic from TQ1 delivery-grade verification.
```

Do not require V1 `examples/openclaw/**` fixtures to be active project fixtures.

### 5.5 `test_package_hygiene_script.py`

Do not modify the hygiene script itself in V2L0-C1.

Replace only its V1-specific test assertions with stronger repository classification checks:

```text
- the generic hygiene checker still detects generic generated artifacts;
- package hygiene remains safe for clean temporary trees;
- V2 source topology and V2L0 history/migration records exist;
- test no longer requires V1 release docs as activity markers.
```

No test may claim `docs/V1_RELEASE_*` establishes current release state.

### 5.6 `test_run_tests_runner.py`

Keep runner robustness tests. Add / update documentation assertions so:

```text
- `run_tests.py` is described as legacy-inclusive diagnostic;
- final V2 delivery acceptance is TQ1 matrix + evidence capsule + verify-ref;
- root docs do not make the legacy runner or V1 CLI a V2 architecture gate.
```

Do not weaken subprocess-harness or test-runner correctness assertions.

---

## 6. Taskbook closure

Commit **exact copies** of both:

```text
docs/delivery/NOLLM_V2L0_LAYER_CONSTITUTION_AND_SOURCE_RECLASSIFICATION_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1_ACTIVE_NAVIGATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
```

Requirements:

```text
- original V2L0 taskbook is copied verbatim from the supplied project task;
- this C1 taskbook is copied verbatim from the supplied C1 task;
- no C:\Users\... path is used as a substitute for committed taskbook content;
- V2L0_DELIVERY_REPORT.md may summarize, but must not be the only task source.
```

Update delivery / validation docs to state the final-evidence lookup rule without self-referential bundle hashes:

```text
final code head:
  <finalHead>

final evidence ref:
  refs/nollm-delivery/tq1-c7r/<finalHead>

authoritative matrix facts:
  parentless evidence capsule

bundle filename and SHA-256:
  external delivery receipt / acceptance audit
```

Do not attempt to put a final bundle SHA into the Git tree before building the bundle.

---

## 7. Required fixed gates

Set:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"
```

Run exactly:

```powershell
python -m pytest -q `
  reference/python/tests/test_v2l0_layer_constitution.py `
  reference/python/tests/test_v2l0_source_reclassification.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_terminology.py `
  reference/python/tests/test_repository_hygiene.py `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_package_hygiene_script.py `
  reference/python/tests/test_run_tests_runner.py
```

Then run exactly:

```powershell
python -m pytest -q `
  reference/python/tests/test_ci1_capture_ingress.py `
  reference/python/tests/test_ci1_capture_policy.py `
  reference/python/tests/test_ci1_capture_visibility.py `
  reference/python/tests/test_cx1_capture_deferred_visibility_validation.py `
  reference/python/tests/test_hcg1_file_first_capture_gateway.py `
  reference/python/tests/test_hcg1_capture_gateway_boundaries.py `
  reference/python/tests/test_hcg1_capture_gateway_cli.py `
  reference/python/tests/test_hx1_trusted_host_bridge.py `
  reference/python/tests/test_hx1_host_binding_preflight.py `
  reference/python/tests/test_hx1_staged_outcomes.py `
  reference/python/tests/test_hx1_receipt_regeneration.py `
  reference/python/tests/test_hx1_boundaries.py `
  reference/python/tests/test_hxa1_final_acceptance_audit.py
```

Capture each command’s complete stdout/stderr and actual exit code in separate raw files before the final evidence build:

```text
v2l0_fixed_gate_raw.txt
v2l0_public_v2_regression_raw.txt
```

The files must contain:

```text
- exact invocation;
- environment variables relevant to execution;
- start/end time;
- original pytest output;
- actual exit status;
- no hand-written replacement summary.
```

If the direct dependency gate hits an external environment execution ceiling, do not write `passed`. Stop and report; do not rely on matrix output as a substitute for a required fixed gate in this implementation task.

---

## 8. Commit and final TQ1 evidence

After fixed gates truly pass:

```powershell
git diff --check
git add -- <allowed paths only>
git commit -m "docs(v2): close active navigation and evidence boundaries"
$finalHead = git rev-parse HEAD
git status --short
```

Run one fresh final-head TQ1 C7R matrix:

```powershell
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$finalHead\v2l0-c1"
$worktreeRoot = "C:\Users\chaos\nollm_test_worktrees\$finalHead"

python reference/python/scripts/run_nollm_test_matrix.py plan `
  --repo-root . `
  --receipt-root $receiptRoot `
  --target-node-count 120 `
  --max-shards 24 `
  --timeout-seconds 3600 `
  *> matrix_plan_raw.txt

python reference/python/scripts/run_nollm_test_matrix.py run-shard `
  --repo-root . `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot `
  --all `
  --workers 4 `
  --timeout-seconds 3600 `
  *> matrix_run_all_raw.txt

python reference/python/scripts/run_nollm_test_matrix.py verify `
  --repo-root . `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot `
  *> matrix_verify_raw.txt
```

The command runner must preserve actual exit status for each command. Do not use `*>` alone if it obscures failure; explicitly capture and check `$LASTEXITCODE`.

Required final matrix facts:

```text
single-pass
plan-frozen timeout=3600
no retry
no receipt overwrite
failed=0
timed_out=0
missing=0
duplicates=0
extras=0
leftovers=0
```

Build a new parentless evidence ref:

```text
refs/nollm-delivery/tq1-c7r/<finalHead>
```

Use the existing sealed packager **without modification**. Populate its existing slots with raw actual files:

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py build-ref `
  --repo-root . `
  --receipt-root $receiptRoot `
  --final-head $finalHead `
  --final-verify-log matrix_verify_raw.txt `
  --governance-file <existing TQ1-C7R governance task> `
  --log "00_environment_and_git_state.txt=environment_git_raw.txt" `
  --log "01_rc_gate_pytest.txt=v2l0_fixed_gate_raw.txt" `
  --log "04_dx1_dg0_dg6_targeted_gate.txt=v2l0_public_v2_regression_raw.txt" `
  --log "05_matrix_plan.txt=matrix_plan_raw.txt" `
  --log "06_matrix_run_all.txt=matrix_run_all_raw.txt" `
  --log "07_matrix_verify.txt=matrix_verify_raw.txt" `
  --log "08_bundle_build_and_audit.txt=bundle_audit_raw.txt" `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead"
```

The legacy file names are accepted packager slots only. Their contents must begin with an honest header identifying the V2L0-C1 command they contain. None may contain:

```text
not produced for this local regression capsule
placeholder
synthetic result
```

In a fresh checkout:

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref `
  --repo-root . `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead" `
  --expected-head $finalHead
```

Then independently inspect the evidence tree and prove:

```text
- original V2L0 taskbook committed in code history;
- C1 taskbook committed in code history;
- all required raw gate and matrix log slots contain actual output;
- no placeholder remains in provided log slots.
```

---

## 9. Single bundle delivery

```powershell
$bundle = "C:\Users\chaos\nollm_v2l0_c1_active_navigation_evidence_closure_20260707_<short-head>.bundle"

git bundle create $bundle --all
git bundle verify $bundle
git fsck --full
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
Get-FileHash $bundle -Algorithm SHA256
git status --short
```

The final bundle must contain:

```text
- V2L0-C1 branch;
- complete reachable history;
- final-head parentless evidence ref;
- V2L0 original taskbook and C1 taskbook in normal code history.
```

No main promotion, no push.

---

## 10. Stop conditions

Stop and report if any of these occurs:

```text
- local main is not 8bb324a...;
- 5e3f9bd... is not current HEAD ancestor;
- a sealed module, test, TQ1 tool or package identity must change;
- a physical V1 / MT1 / OpenClaw / prototype move/delete is required;
- a generic test outside the allowlist requires alteration;
- root docs cannot be de-V1-ed without modifying forbidden source;
- fixed V2L0 gate or direct public V2 regression has a real test failure or timeout;
- raw fixed/regression logs cannot be supplied through existing packager slots;
- final matrix / evidence semantic verify fails;
- HAG branch/evidence must change;
- remote operation, runtime activation, or subagent is required.
```

---

## 11. Completion statement

V2L0-C1 completion means only:

> The active root navigation and ordinary validation guidance now route through V2 layers, V2 public gates and TQ1 evidence. V1 is not presented as a root-level tool surface or validation route. V1/MT1/prototype source remains physically present as retired history; OpenClaw remains a frozen L5/L6 migration asset. The V2L0 taskbook and raw final-head gate evidence are independently recoverable from the committed history and parentless capsule. No Core behavior, HAG integration, runtime activation or main promotion has occurred.

It does not mean:

```text
V1 source has been physically deleted;
OpenClaw is integrated;
HAG is merged or promoted;
automatic admission exists;
global recall exists;
any terminal may bypass HX1;
main has moved.
```
