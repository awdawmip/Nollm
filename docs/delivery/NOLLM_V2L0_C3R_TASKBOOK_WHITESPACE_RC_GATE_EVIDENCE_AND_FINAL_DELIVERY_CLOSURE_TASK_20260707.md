# Nollm V2L0-C3R：任务书格式归一、Engineering RC Gate 证据封装与最终交付闭合任务书

**日期**：2026-07-07
**阶段**：V2L0-C3R — Taskbook Whitespace Normalization / Engineering RC Gate Evidence Binding / Final Delivery Closure
**当前 C3 候选头**：`167c9663888a94185e8631e95f0b60f2d63ad09e`
**活动开发基线**：`8bb324a3a5de46bebb6eadd217820627a971e2a0`
**已接受、未提升组件**：HAG1-C1R `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`
**继续分支**：`codex/v2l0-layer-constitution-source-reclassification`
**执行主体**：单一执行主体；禁止子代理、并行代理和后台任务。
**交付**：一个 complete-history Git bundle + 精确绑定 final code head 的 parentless TQ1 evidence capsule。
**本阶段不做**：不修改 Core、Workflow、Bridge、HCG、HAG、TQ1 runner/packager/verifier、package identity；不删除、移动或重命名 V1/MT1/OpenClaw/旧 Dream-Gravity 文件；不激活 runtime；不提升 main；不执行 fetch/pull/push。

---

## 0. 唯一目标

C3 已证明 V2L0 source classification、legacy-governance test migration、单条 RC hash rebaseline 和 final matrix的技术方向正确，但尚有两项交付纪律缺口：

```text
A. `git diff --check 8bb...finalHead` 仍在五份已提交 taskbook 中发现 39 个 trailing-whitespace violations。

B. Engineering RC focused integrity gate 的 raw log 没有被 capsule 绑定，
   且 V2L0 receipt 没有记录足够的 external-artifact identity。
```

本任务只闭合这两项缺口，并将已知 sealed TQ1 `code_branch` hard-code 问题如实披露为非权威 metadata。

本任务不重做 C1R/C2/C3 的架构判断，不恢复 V1 root navigation，不把旧 Engineering RC 重新称为 active runtime。

---

## 1. 强制开始状态

在 repository root 执行：

```powershell
git switch codex/v2l0-layer-constitution-source-reclassification
git status --short
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git merge-base --is-ancestor 167c9663888a94185e8631e95f0b60f2d63ad09e HEAD
git diff --check
git log --oneline --decorate -10
```

开始条件：

```text
- 当前 branch 必须为 codex/v2l0-layer-constitution-source-reclassification；
- current HEAD 必须为 167c9663888a94185e8631e95f0b60f2d63ad09e，
  或该 commit 必须为 current HEAD 的祖先且其后没有无关提交；
- local main 必须为 8bb324a3a5de46bebb6eadd217820627a971e2a0；
- tracked worktree 必须 clean；
- 不得 fetch / pull / push；
- 不得 reset / rebase / squash / cherry-pick / merge；
- 不得创建平行 C3R branch；
- 不得改写 HAG branch、HAG evidence 或任何 prior evidence ref；
- 不得 main promotion。
```

任一不满足时立即停止并报告 exact status；不得 cleanup、restore、stash、reset 或猜测。

---

## 2. Sealed boundaries

继续 sealed：

```text
DE1, DG1, DG2, DC1, DA1, DF1, DR1, DI1,
CI1, CX1, CX2, BA1, HX1, HCG1, HAG1-C1R, TQ1-C7R。
```

绝对禁止：

```text
- 修改 reference/python/nollm/dream_geometry/**；
- 修改任何 production Python implementation；
- 修改 HCG/HAG/HX/CX2 implementation 或其专属 test；
- 修改 package_nollm_tq1_delivery_evidence.py 或 run_nollm_test_matrix.py；
- 修改 pyproject / package identity；
- 修改 C1R/C2 migrated test logic；
- 恢复 README/ARCHITECTURE/ROADMAP/AGENTS 的 V1 route lock、
  V1 tool table、nollm.cli 或 examples/openclaw 操作导航；
- 删除、移动、重命名任何 legacy source/test/example/docs；
- 激活 OpenClaw/runtime/network/daemon/database/cache/LLM/NLP/embedding/semantic search；
- main promotion、remote Git action、子代理。
```

---

## 3. 唯一允许修改路径

只允许修改或新增：

```text
docs/delivery/NOLLM_V2L0_LAYER_CONSTITUTION_AND_SOURCE_RECLASSIFICATION_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1_ACTIVE_NAVIGATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C1R_V1_ROUTE_LOCK_TEST_MIGRATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C2_MATRIX_LEGACY_GOVERNANCE_TEST_MIGRATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C3_ENGINEERING_RC_HASH_REBASELINE_AND_FINAL_EVIDENCE_CLOSURE_TASK_20260707.md
docs/delivery/NOLLM_V2L0_C3R_TASKBOOK_WHITESPACE_RC_GATE_EVIDENCE_AND_FINAL_DELIVERY_CLOSURE_TASK_20260707.md

docs/delivery/V2L0_DELIVERY_REPORT.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md
```

若需要修改 allowlist 以外任一 tracked path，立即停止并报告 exact path、原因和无法以当前路径完成的具体要求。

---

## 4. Taskbook whitespace normalization

前五份既有 taskbook 的 Markdown **语义内容、字符顺序、段落、代码块、路径、命令、hash、日期和标题均不得变化**。

唯一允许的文本变换：

```text
删除行尾的 ASCII space（U+0020）和 tab（U+0009）。
```

不得：

```text
改写句子；
改变标题、列表、表格或代码块；
合并、拆分、重排文本行；
添加新空行；
改变 UTF-8 编码；
改为 CRLF；
用 “verbatim copy” 作为继续保留 trailing whitespace 的理由。
```

在 repo 外创建临时校验脚本，对每个 taskbook 验证：

```text
before_normalized =
  每行仅删除末尾 ASCII space/tab，以 LF join，保留最终 newline。

after_normalized =
  同一规则下的当前文件内容。

before_normalized == after_normalized
```

只有此证明通过，才可写回。写回后：

```powershell
git diff --name-only
git diff --check
```

此时 tracked diff 只能包含第 3 节路径，且五份既有 taskbook diff 只能显示 trailing-whitespace deletion。

---

## 5. Engineering RC focused integrity gate：绑定真实证据

sealed packager 的 `--log` 只接受固定 `00` 至 `08` slots，不能增加 `09`。本任务指定使用现有合法 slot：

```text
logs/02_rc_export_check.txt
```

内容必须是 C3R 的真实 Engineering RC focused integrity gate raw log。

### 5.1 Fixture 前提

执行只读检查：

```powershell
$required = @(
  "out/nollm_runtime/g_series_engineering_closure_report.json",
  "out/nollm_runtime/gravity_report_demo.json",
  "out/nollm_runtime/minimal_ablation_experiment_report.json",
  "out/nollm_runtime/mode3_trace_experiment_report.json",
  "out/nollm_runtime/multi_step_coverage_report.json",
  "out/nollm_runtime/offset_sampling_report.json",
  "out/nollm_runtime/reverse_cover_report.json"
)

$missing = $required | Where-Object { -not (Test-Path $_) }
$missing
```

若存在缺失：

```text
立即停止并报告；
不得手工伪造 fixture；
不得从 bundle 复制 fixture 到活动 source worktree；
不得修改 RC export/archive code；
不得把 matrix pass 代替 focused gate。
```

### 5.2 Focused gate raw log

设置：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"
```

运行：

```powershell
python -m pytest -q `
  reference/python/tests/test_engineering_rc_artifact_hashes.py `
  reference/python/tests/test_engineering_rc_export.py `
  reference/python/tests/test_engineering_rc_archive.py `
  reference/python/tests/test_engineering_rc_final_smoke.py
```

保存为：

```text
v2l0_c3r_engineering_rc_integrity_raw.txt
```

此 raw log 必须包括：

```text
V2L0-C3R Engineering RC focused integrity gate raw log
exact invocation
PYTHONDONTWRITEBYTECODE
PYTEST_DISABLE_PLUGIN_AUTOLOAD
PYTHONPATH
start/end RFC3339
original stdout/stderr
actual exit_code
```

focused gate 必须通过。若 failure、timeout 或环境时限中断，立即停止且不得提交。

### 5.3 Receipt 记录

更新 `validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md`，记录：

```text
focused gate exact command；
result summary；
raw-log SHA-256；
capsule destination = logs/02_rc_export_check.txt；
slot name 是 sealed legacy layout，不表示只运行 export checker。
```

---

## 6. C3R taskbook与报告更新

新增：

```text
docs/delivery/NOLLM_V2L0_C3R_TASKBOOK_WHITESPACE_RC_GATE_EVIDENCE_AND_FINAL_DELIVERY_CLOSURE_TASK_20260707.md
```

更新：

```text
docs/delivery/V2L0_DELIVERY_REPORT.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md
```

必须准确记载：

```text
C3 code head 167c966... 不是 final C3R evidence head；
C3R 只做 taskbook whitespace normalization 与 evidence binding；
C3 RC rebaseline remains exactly one record: test_geometry.py；
V2L0 remains candidate until C3R acceptance audit；
HAG1-C1R remains accepted / unpromoted；
Engineering RC remains historical matrix input；
actual branch truth = code_head + evidence_ref + logs/00；
capsule code_branch 是已知 inherited non-authoritative field。
```

---

## 7. Fresh fixed gates

### 7.1 V2L0 fixed gate

运行并保存：

```text
v2l0_c3r_fixed_gate_raw.txt
```

```powershell
python -m pytest -q `
  reference/python/tests/test_v2l0_layer_constitution.py `
  reference/python/tests/test_v2l0_source_reclassification.py `
  reference/python/tests/test_v1_route_lock.py `
  reference/python/tests/test_v1_docs_consistency.py `
  reference/python/tests/test_dg0_v2_module_boundaries.py `
  reference/python/tests/test_dg7_runtime_boundaries.py `
  reference/python/tests/test_geometry.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_terminology.py `
  reference/python/tests/test_repository_hygiene.py `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_package_hygiene_script.py `
  reference/python/tests/test_run_tests_runner.py
```

### 7.2 Public V2 regression

运行并保存：

```text
v2l0_c3r_public_v2_regression_raw.txt
```

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

### 7.3 TQ1 helper self-test slot

为避免 `logs/03_tq1_self_tests.txt` 再次是 placeholder，运行：

```powershell
python -m pytest -q reference/python/tests/test_nollm_test_shards.py
```

保存：

```text
v2l0_c3r_tq1_helper_self_test_raw.txt
```

第 5、7 节每份 raw log 必须含 exact invocation、relevant environment、start/end RFC3339、original stdout/stderr、actual exit code。

任一 gate 失败、超时或环境时限中断，即刻停止；不得提交或运行 final matrix。

---

## 8. Commit 与 final range cleanliness

仅在第 4、5、7 节全部通过后：

```powershell
git diff --check
git add -- <allowed paths only>
git commit -m "docs(v2): close taskbook whitespace and RC gate evidence"
$finalHead = git rev-parse HEAD
git status --short
```

随后必须运行：

```powershell
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
if ($LASTEXITCODE -ne 0) {
  throw "Final base-to-head diff check failed."
}
```

该命令不得以无范围的 `git diff --check` 替代。

---

## 9. Fresh final matrix 与 capsule

运行 fresh final-head matrix：

```powershell
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$finalHead\v2l0-c3r"
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

逐一检查三个 exit code。任一非零：

```text
立即停止；
不得 build evidence；
不得 bundle；
不得覆盖 receipt；
不得调整 collection、worker、timeout 或重试策略规避失败。
```

最终必须满足：

```text
single-pass
plan-frozen timeout = 3600
no retry
no receipt overwrite
failed = 0
timed_out = 0
missing = 0
duplicates = 0
extras = 0
leftovers = 0
```

### 9.1 Capsule log mapping

不得改 packager。使用：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py build-ref `
  --repo-root . `
  --receipt-root $receiptRoot `
  --final-head $finalHead `
  --final-verify-log matrix_verify_raw.txt `
  --governance-file <existing TQ1-C7R governance task> `
  --log "00_environment_and_git_state.txt=environment_git_raw.txt" `
  --log "01_rc_gate_pytest.txt=v2l0_c3r_fixed_gate_raw.txt" `
  --log "02_rc_export_check.txt=v2l0_c3r_engineering_rc_integrity_raw.txt" `
  --log "03_tq1_self_tests.txt=v2l0_c3r_tq1_helper_self_test_raw.txt" `
  --log "04_dx1_dg0_dg6_targeted_gate.txt=v2l0_c3r_public_v2_regression_raw.txt" `
  --log "05_matrix_plan.txt=matrix_plan_raw.txt" `
  --log "06_matrix_run_all.txt=matrix_run_all_raw.txt" `
  --log "07_matrix_verify.txt=matrix_verify_raw.txt" `
  --log "08_bundle_build_and_audit.txt=pre_bundle_range_audit_raw.txt" `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead"
```

`pre_bundle_range_audit_raw.txt` 必须真实记录：

```text
git status --short
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
git fsck --full
git rev-parse main
git rev-parse origin/main
git branch --show-current
```

不得出现：

```text
placeholder
not produced for this local regression capsule
synthetic result
```

fresh checkout verify：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref `
  --repo-root . `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead" `
  --expected-head $finalHead
```

人工核验：

```text
logs/02 含 focused RC gate raw output；
logs/03 含真实 helper self-test；
logs/08 含 base-to-final range diff check；
五份 earlier taskbooks 无 trailing whitespace；
C3R taskbook 在 normal code tree；
code_head/evidence_ref/logs/00 branch 相互一致；
capsule code_branch 不作为 branch truth。
```

---

## 10. One complete-history bundle

```powershell
$bundle = "C:\Users\chaos\nollm_v2l0_c3r_taskbook_whitespace_rc_gate_evidence_closure_20260707_<short-head>.bundle"

git bundle create $bundle --all
git bundle verify $bundle
git fsck --full
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
Get-FileHash $bundle -Algorithm SHA256
git status --short
```

最终 bundle 必须包含：

```text
V2L0 branch
complete reachable history
final-head parentless evidence ref
V2L0, C1, C1R, C2, C3, C3R taskbooks
no uncommitted changes
```

不得 main promotion，不得 push。

---

## 11. Stop conditions

任一发生立即停止并报告：

```text
local main 不等于 8bb324a...；
current branch / HEAD 不符合第 1 节；
tracked worktree 不 clean；
whitespace normalization 改变任何非尾随空白内容；
Engineering RC fixture 不完整；
focused RC gate / fixed gate / public regression / helper self-test failure、timeout 或环境时限中断；
任一 allowlist 外文件需要修改；
base-to-final diff check 非零；
final matrix 非零；
evidence verify-ref 失败；
HAG branch/evidence 必须改变；
需要 remote Git、runtime activation、subagent 或 TQ1 tool modification。
```

---

## 12. 完成后的准确表述

V2L0-C3R 完成后仅可表述：

> V2L0 的 active navigation、legacy-governance test migration、restricted historical RC manifest rebaseline、taskbook format cleanliness 和 gate-evidence binding 均已在同一 final-head capsule 中闭合。V1/MT1/prototype 仍物理存在但已 retired；OpenClaw legacy 仍是 frozen L5/L6 migration asset。Engineering RC 仍仅是历史 matrix input；HAG1-C1R 仍为 accepted / unpromoted。Core 未修改，runtime 未激活，main 未移动。

不得表述：

```text
V1 source 已删除；
OpenClaw 已接入；
Engineering RC 是当前 production runtime；
HAG 已合并/main；
automatic admission 或 global recall 已启用；
terminal 可绕过 HX1；
main 已移动。
```
