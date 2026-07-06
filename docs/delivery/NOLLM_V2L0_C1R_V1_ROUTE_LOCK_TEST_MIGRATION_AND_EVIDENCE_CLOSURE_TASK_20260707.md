# Nollm V2L0-C1R：V1 Route-Lock 测试迁移、活动导航闭合与证据闭合任务书

**日期**：2026-07-07  
**阶段**：V2L0-C1R — V1 Route-Lock Test Migration / Active Navigation Closure / Evidence Closure  
**前一候选代码头**：`5e3f9bd4547d2c6b0797b0f1ef82544be33aa7dc`  
**活动开发基线**：`8bb324a3a5de46bebb6eadd217820627a971e2a0`  
**已接受、未提升组件**：HAG1-C1R `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`  
**继续分支**：`codex/v2l0-layer-constitution-source-reclassification`  
**执行主体**：单一执行主体；禁止子代理、并行代理、后台任务。  
**交付**：一个 complete-history Git bundle + 精确绑定 final code head 的 parentless TQ1 evidence capsule。  
**本阶段不做**：不删除/移动 V1、MT1、旧 Dream/Gravity prototype 或 OpenClaw 文件；不改 sealed production；不合并或修改 HAG1-C1R；不提升 main；不执行 fetch/pull/push。

---

## 0. 本修订为什么必要

V2L0-C1 已正确停止，未提交。

停止原因不是 root docs 去 V1 化方向错误，而是前一任务书遗漏了完整 TQ1 matrix 仍会收集的两份 V1-current 测试：

```text
reference/python/tests/test_v1_route_lock.py
reference/python/tests/test_v1_docs_consistency.py
```

这两份测试要求 root docs 保留：

```text
Nollm V1 Route Lock
V1 tool action appendix
nollm.cli
examples/openclaw
```

因此，若不修改它们，root docs 就不得不继续将 V1 作为日常可执行路线，直接破坏 V2L0 的唯一目标：

```text
V2 is the only active architecture.
V1 / MT1 / pre-V2 prototype are retired history.
OpenClaw legacy is a frozen L5/L6 migration asset.
```

本任务授权将上述两份测试加入 allowlist，并将它们从“V1 路线锁定测试”转换为“V1 已退役、不得重新出现在活动导航中的回归测试”。

这不是通过删除测试缩小覆盖；恰恰相反，它将完整矩阵中原先强制 V1-current 的测试改为强制 V2.2 当前分类。

---

## 1. 当前工作树状态：允许继续，但不得丢弃

本任务开始时，工作树**预期不干净**。已报告的未提交变更为：

```text
README.md
ARCHITECTURE.md
ROADMAP.md
AGENTS.md
docs/delivery/NOLLM_V2L0_LAYER_CONSTITUTION_AND_SOURCE_RECLASSIFICATION_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1_ACTIVE_NAVIGATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
```

这些是前一轮已正确开始、但因 allowlist 缺口而停止的 V2L0-C1 工作成果；必须保留并继续完成。

### 1.1 强制开始检查

```powershell
git switch codex/v2l0-layer-constitution-source-reclassification
git status --short
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git merge-base --is-ancestor 5e3f9bd4547d2c6b0797b0f1ef82544be33aa7dc HEAD
git diff --check
git diff --name-only
git ls-files --others --exclude-standard
```

开始条件：

```text
- 当前分支必须为 codex/v2l0-layer-constitution-source-reclassification；
- 5e3f9bd... 必须是当前 HEAD 的祖先；
- local main 必须精确为 8bb324a...；
- 不得 fetch / pull / push；
- 不得创建平行 C1R 分支；
- 不得 reset / rebase / squash / cherry-pick / merge；
- 不得 stash、checkout --、restore、clean，或用任何方式丢弃前一轮未提交变更；
- tracked/untracked changes 必须仅位于第 1 节列出的六个预期路径。
```

若发现任何额外改动、任何预期路径缺失，或 local main 不等于 `8bb324a...`，立即停止并报告精确状态。不得猜测、覆盖或清理工作树。

---

## 2. 唯一目标

完成以下三件事，并且只完成这些事：

```text
A. 使 root navigation 与 ordinary validation guidance 不再把 V1 CLI、
   V1 tool actions 或 examples/openclaw 作为活动工作入口；

B. 将 test_v1_route_lock.py 与 test_v1_docs_consistency.py
   迁移为更强的 V2.2 retirement / classification regression，
   使完整矩阵不再反向要求 V1 current；

C. 将 V2L0、V2L0-C1、V2L0-C1R 三份任务书提交进正常代码历史，
   并用现有 sealed packager 的 --log 能力封入真实 fixed-gate、
   V2 regression、matrix plan/run/verify 原始日志。
```

本阶段不做 V1 物理删除，不实现 OpenClaw adapter，不改 package identity，不修改 Core 行为，也不进行 HAG integration / promotion。

---

## 3. Sealed baseline 与禁止事项

继续 sealed：

```text
DE1, DG1, DG2, DC1, DA1, DF1, DR1, DI1,
CI1, CX1, CX2, BA1, HX1, HCG1,
HAG1-C1R, TQ1-C7R。
```

绝对禁止：

```text
- 修改 reference/python/nollm/dream_geometry/**；
- 修改 HCG / HAG / HX1 / CX2 implementation 或其专属 tests；
- 修改 TQ1 runner、packager、verifier；
- 删除、移动、重命名任何 V1 / MT1 / OpenClaw / prototype source、tests、examples 或 scripts；
- 修改 pyproject / package identity；
- 激活 OpenClaw runtime、network、daemon、database、cache、LLM、NLP、embedding、semantic search；
- 让 V2 Core import V1 或 terminal code；
- main promotion；
- 远程 Git 操作；
- 子代理。
```

---

## 4. 允许修改路径

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
docs/delivery/NOLLM_V2L0_C1R_V1_ROUTE_LOCK_TEST_MIGRATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md

reference/python/tests/test_v2l0_layer_constitution.py
reference/python/tests/test_v2l0_source_reclassification.py
reference/python/tests/test_architecture_language.py
reference/python/tests/test_terminology.py
reference/python/tests/test_repository_hygiene.py
reference/python/tests/test_package_hygiene_script.py
reference/python/tests/test_run_tests_runner.py

reference/python/tests/test_v1_route_lock.py
reference/python/tests/test_v1_docs_consistency.py
```

`test_v1_route_lock.py` 与 `test_v1_docs_consistency.py` 是本修订新增的唯一 allowlist 授权。

若任一其他文件、测试或脚本需要修改，立即停止并报告 exact path、test name、assertion 和阻断原因。

---

## 5. Root navigation 闭合

### 5.1 Root docs 不得继续承担 V1 操作手册角色

从以下 root docs 删除所有完整 V1 route-lock、V1 action table、V1 CLI 操作说明和 OpenClaw legacy fixture 的执行导航：

```text
README.md
ARCHITECTURE.md
ROADMAP.md
AGENTS.md
```

root docs 可以保留**一句**历史指针：

```text
V1 / MT1 / pre-V2 prototype source remains physically present as retired history;
see docs/history/ for classification and migration boundaries.
```

root docs 不得包含下列任何内容：

```text
Nollm V1 Route Lock
Stable historical V1 tool actions
nollm.validate
nollm.orient
nollm.surface
nollm.focus
nollm.recall
nollm.read_card
nollm.write_card
nollm.cli
examples/openclaw
完整 V1 Card / Anchor / Ledger / tool route 说明
```

V1 的完整历史操作细节不应复制至 `docs/history`；Git history 是其完整档案。`docs/history/V1_RETIREMENT_RECORD.md` 只保存边界、分类、最后适用 ref/tag（如已知）和不可回流规则。

### 5.2 AGENTS 的日常验证必须 V2-first

删除：

```powershell
python -m nollm.cli validate ../../examples/openclaw
python -m nollm.cli audit ../../examples/openclaw
```

`AGENTS.md` 中 ordinary repository validation 只能列出：

```text
- component-local V2 pytest gates；
- CI1/CX1/HCG1/HX1 public regression gates；
- final-head TQ1 matrix、parentless evidence capsule、fresh verify-ref。
```

`python run_tests.py` 可以保留，但必须明确标注：

```text
legacy-inclusive repository diagnostic；
not the primary V2 component acceptance gate；
not evidence that V1 is active architecture。
```

不得在 root docs 将旧 runner、V1 CLI 或 OpenClaw fixture称为 V2 semantic acceptance 的必要操作。

### 5.3 Root docs 的必备正向内容

四份 root docs 必须明确：

```text
V2 is the only active architecture.
protocol/v2 is the only active protocol root.
V1 / MT1 / pre-V2 prototype are retired history.
OpenClaw legacy is a frozen L5/L6 migration asset, not current runtime.
Core does not import adapters or terminals.
Adapters do not own facts.
Terminals do not bypass L4.
HCG1 is accepted L5 File Capture Adapter.
HAG1-C1R is accepted / unpromoted L5 File Admission Adapter.
V2L0-C1R neither merges nor modifies HAG1-C1R.
```

不得声称：

```text
HAG 已并入 main；
OpenClaw 已接入；
自动 admission 已授权；
runtime / daemon 已启动；
V1 source 已删除。
```

---

## 6. 两份 V1 route-lock 测试的授权性迁移

### 6.1 `test_v1_route_lock.py`

文件名可以保留，以保持历史可追溯和测试 collection 稳定；但其 docstring、测试函数名、断言和 failure message 必须明确表达新语义：

```text
V1 route is locked out of active navigation;
it is not locked in as the current route.
```

禁止继续要求 root docs 包含：

```text
Nollm V1 Route Lock
Stable historical V1 tool actions
nollm.* tool table
nollm.cli
examples/openclaw
```

必须新增/替换为以下断言：

```text
1. README / ARCHITECTURE / ROADMAP / AGENTS 均不包含第 5.1 节禁止字符串；
2. 每份 root doc 都明确：
   - V2 is the only active architecture；
   - protocol/v2 is active protocol root；
   - V1/MT1/prototype are retired history；
3. `docs/history/V1_RETIREMENT_RECORD.md` 存在，并说明：
   - V1 source may remain physically present temporarily；
   - Git history is canonical full archive；
   - V1 compatibility imports must not enter V2 Core；
4. 该测试不得要求 V1 CLI 或 V1 tool manifest 作为当前入口存在；
5. 该测试不得把 V1 test collection 的存在解释为 V1 current status。
```

该测试应检测“未来有人把 V1 tool appendix 重新写回 root docs”的回归，而不是保护 V1 继续活动。

### 6.2 `test_v1_docs_consistency.py`

保留文件名，但将内容改为“历史文档分类一致性”：

```text
1. `protocol/v2/LAYER_CONSTITUTION.md`、`protocol/v2/LEGACY_BOUNDARY.md`、
   V1 retirement record、OpenClaw migration record 均存在；
2. 四份 root docs 与上述 records 对 V1/MT1/prototype/OpenClaw 的分类一致；
3. OpenClaw 被写为：
   frozen L5/L6 migration asset；
   not current runtime；
   not V2 Core；
4. `protocol/v2` 被写为唯一 active protocol root；
5. root docs 不链接、不引用或不要求 V1 CLI / tool action / examples/openclaw；
6. 文档可以承认 legacy files 物理存在，
   但不得因此称 V1 stable/current/parallel active；
7. 不得以 V1 release docs、OpenClaw fixture、旧 route-lock appendix
   作为当前项目活跃性证据。
```

禁止删除、skip 或 `xfail` 任一原 V1 test；应把它们改造成更严格的 V2 activity-boundary tests。

### 6.3 其他 generic tests

此前 C1 allowlist 中的下列 generic tests继续按 V2.2 分类目标修订：

```text
test_v2l0_layer_constitution.py
test_v2l0_source_reclassification.py
test_architecture_language.py
test_terminology.py
test_repository_hygiene.py
test_package_hygiene_script.py
test_run_tests_runner.py
```

要求：

```text
- 继续检查 V2 root navigation；
- 不要求 examples/openclaw、V1 route-lock 或 V1 docs 作为活动资产；
- `run_tests.py` 仅被描述为 legacy-inclusive diagnostic；
- TQ1 matrix + capsule + verify-ref 是 delivery-grade acceptance；
- 禁止通过删掉所有 legacy 相关断言来降低质量；
- 任何由 V1-current 替换的断言必须有 V2.2 更强的正向分类断言。
```

---

## 7. Taskbook committed-history 闭合

正常代码历史必须包含**逐字复制**的三份任务书：

```text
docs/delivery/NOLLM_V2L0_LAYER_CONSTITUTION_AND_SOURCE_RECLASSIFICATION_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1_ACTIVE_NAVIGATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1R_V1_ROUTE_LOCK_TEST_MIGRATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
```

要求：

```text
- 原 V2L0 taskbook 按 supplied original verbatim copy；
- 原 V2L0-C1 taskbook 按 supplied original verbatim copy；
- 本 C1R taskbook 按 supplied original verbatim copy；
- 不得以 C:\Users\... 或任何 machine-local path 代替任务书内容；
- V2L0_DELIVERY_REPORT 可以总结，但不能是唯一 task source。
```

更新 `docs/delivery/V2L0_DELIVERY_REPORT.md` 与 `docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md`：

```text
final code head:
  <finalHead>

final evidence ref:
  refs/nollm-delivery/tq1-c7r/<finalHead>

authoritative final matrix facts:
  parentless evidence capsule

bundle filename and SHA-256:
  external delivery receipt / acceptance audit
```

不得尝试在 Git tree 内预写最终 bundle SHA；这会形成不可能的自引用循环。

---

## 8. 固定门禁与原始日志

设置：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"
```

### 8.1 V2L0-C1R fixed gate

运行：

```powershell
python -m pytest -q `
  reference/python/tests/test_v2l0_layer_constitution.py `
  reference/python/tests/test_v2l0_source_reclassification.py `
  reference/python/tests/test_v1_route_lock.py `
  reference/python/tests/test_v1_docs_consistency.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_terminology.py `
  reference/python/tests/test_repository_hygiene.py `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_package_hygiene_script.py `
  reference/python/tests/test_run_tests_runner.py
```

### 8.2 Public V2 regression

运行：

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

### 8.3 原始日志要求

在 final evidence build 前，分别保存：

```text
v2l0_c1r_fixed_gate_raw.txt
v2l0_c1r_public_v2_regression_raw.txt
```

每份日志必须包含：

```text
- exact invocation；
- PYTHONDONTWRITEBYTECODE、PYTEST_DISABLE_PLUGIN_AUTOLOAD、PYTHONPATH；
- start/end RFC3339 timestamps；
- original stdout/stderr；
- actual process exit code；
- no manually written substituted summary。
```

若任何 fixed gate / public regression 出现真实 failure、timeout 或外部环境上限中断：

```text
立即停止；
不得把 matrix pass 代替 required fixed gate；
不得在日志中写 passed；
不得提交。
```

---

## 9. Commit、final matrix、capsule 和单 bundle

### 9.1 Commit

fixed gates 完整通过后：

```powershell
git diff --check
git add -- <allowed paths only>
git commit -m "docs(v2): retire V1 route lock from active navigation"
$finalHead = git rev-parse HEAD
git status --short
```

### 9.2 Fresh final-head matrix

```powershell
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$finalHead\v2l0-c1r"
$worktreeRoot = "C:\Users\chaos\nollm_test_worktrees\$finalHead"

python reference/python/scripts/run_nollm_test_matrix.py plan `
  --repo-root . `
  --receipt-root $receiptRoot `
  --target-node-count 120 `
  --max-shards 24 `
  --timeout-seconds 3600 `
  *> matrix_plan_raw.txt
$planExit = $LASTEXITCODE

python reference/python/scripts/run_nollm_test_matrix.py run-shard `
  --repo-root . `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot `
  --all `
  --workers 4 `
  --timeout-seconds 3600 `
  *> matrix_run_all_raw.txt
$runExit = $LASTEXITCODE

python reference/python/scripts/run_nollm_test_matrix.py verify `
  --repo-root . `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot `
  *> matrix_verify_raw.txt
$verifyExit = $LASTEXITCODE
```

对三个 `$*Exit` 必须逐一检查。任一非零即停止，不得 build evidence。

最终矩阵必须证明：

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

### 9.3 Parentless evidence capsule

使用现有 sealed packager，不得修改其代码。将真实日志填入现有 slots：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py build-ref `
  --repo-root . `
  --receipt-root $receiptRoot `
  --final-head $finalHead `
  --final-verify-log matrix_verify_raw.txt `
  --governance-file <existing TQ1-C7R governance task> `
  --log "00_environment_and_git_state.txt=environment_git_raw.txt" `
  --log "01_rc_gate_pytest.txt=v2l0_c1r_fixed_gate_raw.txt" `
  --log "04_dx1_dg0_dg6_targeted_gate.txt=v2l0_c1r_public_v2_regression_raw.txt" `
  --log "05_matrix_plan.txt=matrix_plan_raw.txt" `
  --log "06_matrix_run_all.txt=matrix_run_all_raw.txt" `
  --log "07_matrix_verify.txt=matrix_verify_raw.txt" `
  --log "08_bundle_build_and_audit.txt=bundle_audit_raw.txt" `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead"
```

legacy filename仅是 sealed packager 的 slot 名；每个填入内容的首行都必须真实说明该文件保存的 V2L0-C1R command。

以下字符串不得出现在 supplied log slots：

```text
not produced for this local regression capsule
placeholder
synthetic result
```

fresh checkout：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref `
  --repo-root . `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead" `
  --expected-head $finalHead
```

并人工检查：

```text
- 三份 taskbook 都在 final normal code tree；
- fixed gate / regression / matrix log slots 含真实输出；
- supplied log slots 中无 placeholder；
- final evidence code head 与 final Git head 精确一致。
```

### 9.4 Single bundle delivery

```powershell
$bundle = "C:\Users\chaos\nollm_v2l0_c1r_v1_route_lock_navigation_evidence_closure_20260707_<short-head>.bundle"

git bundle create $bundle --all
git bundle verify $bundle
git fsck --full
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
Get-FileHash $bundle -Algorithm SHA256
git status --short
```

最终 bundle 必须包含：

```text
- V2L0-C1R branch；
- full reachable history；
- final-head parentless evidence ref；
- 三份 taskbook 的 normal code history；
- 不含未提交工作树变化。
```

不得 main promotion，不得 push。

---

## 10. 停止条件

出现任一项立即停止并报告：

```text
- 当前 dirty worktree 不等于第 1 节允许的预期集合；
- local main 不是 8bb324a...；
- 5e3f9bd... 不是 current HEAD 祖先；
- 任何 sealed production module、HAG/HCG/HX/CX2 test、TQ1 tool 或 package metadata 需要修改；
- 任何 allowlist 外路径需要修改；
- V1 / MT1 / OpenClaw / prototype 文件需要移动、删除或重命名；
- root docs 无法去 V1 化而不改变禁止路径；
- fixed gate 或 public V2 regression 出现真实 failure/timeout/环境时限中断；
- 无法通过现有 --log slots 提供真实 gate logs；
- matrix、capsule semantic verify 或 bundle verification 失败；
- HAG branch/evidence 需要改动；
- 需要远程操作、runtime activation 或子代理。
```

---

## 11. 完成后的准确表述

V2L0-C1R 完成后仅可表述：

> Nollm 的 root navigation、普通验证指引、V1 route-lock tests 和历史分类现已一致地将 V2 定义为唯一活动架构。V1/MT1/prototype 物理文件仍暂存于工作树，但只能作为 retired history；OpenClaw legacy 是冻结的 L5/L6 migration asset。完整 TQ1 matrix 仍收集经迁移后的 V1 route-lock tests，因此 V1 不会被静默排除，而是被明确约束为不再作为活动路线。V2L0-C1R 未修改 Core、未物理删除旧源、未激活 runtime、未合并或提升 HAG、未移动 main。

不得表述：

```text
V1 source has been deleted；
OpenClaw is integrated；
HAG is merged/main；
automatic admission exists；
global recall exists；
terminal may bypass HX1；
main has moved。
```
