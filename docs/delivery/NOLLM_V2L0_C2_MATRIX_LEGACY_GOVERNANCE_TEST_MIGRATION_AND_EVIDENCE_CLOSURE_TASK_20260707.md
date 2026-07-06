# Nollm V2L0-C2：矩阵遗留治理测试迁移、Canonical 边界闭合与证据交付任务书

**日期**：2026-07-07  
**阶段**：V2L0-C2 — Matrix Legacy Governance-Test Migration / Canonical Boundary Closure / Evidence Delivery  
**当前 V2L0-C1R 候选头**：`242bf0d74c149309b66fa7e0ca97e6adfd36b6a1`  
**活动开发基线**：`8bb324a3a5de46bebb6eadd217820627a971e2a0`  
**已接受、未提升组件**：HAG1-C1R `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`  
**继续分支**：`codex/v2l0-layer-constitution-source-reclassification`  
**执行主体**：单一执行主体；不得使用子代理、并行代理或后台任务。  
**交付形式**：一个 complete-history Git bundle，且包含精确绑定 final code head 的 parentless TQ1 evidence capsule。  
**本任务不做**：不删除、移动或重命名 V1、MT1、旧 Dream/Gravity prototype、OpenClaw 源码／测试／examples；不修改 sealed production；不合并 HAG；不提升 main；不进行 fetch/pull/push。

---

## 0. 本任务的来由与唯一目标

V2L0-C1R 已在 `242bf0d...` 形成一个干净的普通代码提交，且两个直接固定门禁已经真实通过：

```text
V2L0-C1R fixed gate: 38 passed
public V2 regression: 109 passed
```

但 final-head TQ1 matrix 的 24 个 shard 中有 3 个失败。失败不是 Core 行为问题，而是完整矩阵仍收集三份旧治理测试；这些测试把已被 V2L0 正确移出的 root-level 历史文本当作当前必需内容：

```text
reference/python/tests/test_dg0_v2_module_boundaries.py
  要求 root governance 保留 “Dream Geometry V2 Route Lock”。

reference/python/tests/test_dg7_runtime_boundaries.py
  要求 ROADMAP.md 保留 DG5 / DG6 / DG7 的旧交付事实句。

reference/python/tests/test_geometry.py
  要求 AGENTS.md 保留 D1 pure-polygon-overlap 的旧边界句。
```

上述测试不在 C1R allowlist，因此前一轮停止正确。

本任务唯一目标是：**将这三份测试由“旧 root-document wording lock”迁移为“当前 V2 canonical-document boundary lock”，而不把旧文本重新塞回 README、ARCHITECTURE、ROADMAP 或 AGENTS。**

目标不是删除旧测试，更不是降低完整矩阵覆盖。每一份测试都必须保留，并改为验证更强、更正确、更接近当前 V2.1/V2.2 架构的事实：

```text
DG0:
  V2 优先权与活动架构归属由 protocol/v2 的 constitution 层定义，
  而不是由 root docs 中的旧 Route Lock 文字定义。

DG7:
  DG5 / DG6 / DG7 的 sealed validation / reference-runtime 历史状态
  由 V2.2 component progress table 和 validation/docs 分类定义，
  而不是由 root ROADMAP 的旧交付句定义。

Geometry:
  DG1 的纯确定性几何边界由 protocol/v2 canonical boundary 定义，
  而不是由 AGENTS 的历史 D1 wording 定义。
```

本任务完成前，V2L0 仍是 candidate；不得声称已接受。

---

## 1. 开始状态与分支纪律

开始前必须执行：

```powershell
git switch codex/v2l0-layer-constitution-source-reclassification
git status --short
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git merge-base --is-ancestor 242bf0d74c149309b66fa7e0ca97e6adfd36b6a1 HEAD
git diff --check
git log --oneline --decorate -8
```

开始条件：

```text
- 当前分支必须为 codex/v2l0-layer-constitution-source-reclassification；
- current HEAD 必须精确为 242bf0d74c149309b66fa7e0ca97e6adfd36b6a1，
  或者 242bf0d... 必须是当前 HEAD 的祖先，且其后没有任何不属于本任务的提交；
- local main 必须精确为 8bb324a3a5de46bebb6eadd217820627a971e2a0；
- tracked worktree 必须 clean；
- 不得将 bundle 内 remote-tracking ref 当作 live origin/main 事实；
- 不得 fetch / pull / push；
- 不得创建平行 C2 分支；
- 不得 reset / rebase / squash / cherry-pick / merge；
- 不得修改 HAG branch 或其 evidence ref；
- 不得 main promotion。
```

若以下任一项不成立，立即停止并报告，不得修复：

```text
local main 不等于 8bb324a...；
242bf0d... 不可达；
worktree 不干净；
出现未知额外提交；
任何 remote operation 已发生。
```

---

## 2. 已封板边界与绝对禁止项

继续 sealed：

```text
DE1
DG1
DG2
DC1
DA1
DF1
DR1
DI1
CI1
CX1
CX2
BA1
HX1
HCG1
HAG1-C1R
TQ1-C7R
```

绝对禁止：

```text
- 修改 reference/python/nollm/dream_geometry/**；
- 修改 HCG / HAG / HX1 / CX2 implementation 或其专属 tests；
- 修改 TQ1 runner、packager、verifier；
- 修改 pyproject / package identity；
- 删除、移动、重命名任何 legacy source、test、fixture、example、script 或 docs directory；
- 恢复 root-level V1 route lock、V1 tool action appendix、nollm.cli 或 examples/openclaw 操作说明；
- 将 OpenClaw legacy 写成 current runtime 或 V2 Core；
- 激活 OpenClaw、network、daemon、database、cache、LLM、NLP、embedding 或 semantic search；
- main promotion；
- 远程 Git 操作；
- 使用子代理。
```

---

## 3. 允许修改路径

仅允许修改或新增：

```text
protocol/v2/LAYER_CONSTITUTION.md
protocol/v2/LEGACY_BOUNDARY.md

docs/architecture/NOLLM_PROJECT_BOOK_V2_2_LAYERED_CORE_TO_TERMINAL.md
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
docs/project/NOLLM_SOURCE_TOPOLOGY_V2.md
docs/history/V1_RETIREMENT_RECORD.md
docs/history/OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/delivery/V2L0_DELIVERY_REPORT.md
docs/delivery/NOLLM_V2L0_C2_MATRIX_LEGACY_GOVERNANCE_TEST_MIGRATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md

reference/python/tests/test_v2l0_layer_constitution.py
reference/python/tests/test_v2l0_source_reclassification.py
reference/python/tests/test_architecture_language.py
reference/python/tests/test_terminology.py
reference/python/tests/test_repository_hygiene.py
reference/python/tests/test_package_hygiene_script.py
reference/python/tests/test_run_tests_runner.py

reference/python/tests/test_dg0_v2_module_boundaries.py
reference/python/tests/test_dg7_runtime_boundaries.py
reference/python/tests/test_geometry.py
```

其中新增授权的唯一 legacy-governance test 文件为：

```text
test_dg0_v2_module_boundaries.py
test_dg7_runtime_boundaries.py
test_geometry.py
```

若需要修改任何 allowlist 外路径，立即停止并报告：

```text
exact path
test name / assertion
为什么 current canonical docs 无法满足
为什么该路径不在 allowlist
```

不得“顺手扩大”范围。

---

## 4. Canonical document placement rules

### 4.1 Root docs 的地位

以下 root docs 已在 `242bf0d...` 去 V1 化：

```text
README.md
ARCHITECTURE.md
ROADMAP.md
AGENTS.md
```

本任务不得重新增加旧 V1 操作导航，也不要求它们承载完整 DG0/DG7/D1 历史细节。

root docs 的职责仅为：

```text
- 导向 V2.2 active architecture；
- 指向 protocol/v2、component progress、source topology、history/migration records；
- 描述 ordinary V2 validation 和 final TQ1 delivery discipline；
- 禁止 terminal bypass L4；
- 标明 V1/MT1/prototype retired、OpenClaw frozen migration asset。
```

### 4.2 Canonical location map

| 事实 | 唯一／主要 canonical location | root docs 是否需逐字复述 |
|---|---|---:|
| V2 是唯一活动架构、L0–L6 单向依赖 | `protocol/v2/LAYER_CONSTITUTION.md` | 否；仅摘要与链接 |
| V1/MT1/prototype retired、OpenClaw migration asset | `protocol/v2/LEGACY_BOUNDARY.md` + `docs/history/**` | 否；仅摘要与链接 |
| DG0 V2 priority / boundary governance | `protocol/v2/LAYER_CONSTITUTION.md` + `protocol/v2/CONSTITUTION.md` | 否 |
| DG1 pure deterministic geometry boundary | `protocol/v2/LAYER_CONSTITUTION.md` | 否 |
| DG5/DG6/DG7 当前 sealed-validation / historical status | `docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md` | 否 |
| final delivery / evidence lookup rule | `docs/delivery/V2L0_DELIVERY_REPORT.md` | 否；root docs 仅指向 TQ1 process |

任何测试不得再把 root docs 当作所有历史协议与验证事实的唯一存放点。

---

## 5. 三份矩阵失败测试的严格迁移

## 5.1 `test_dg0_v2_module_boundaries.py`

### 被替代的旧断言

删除／替换任何要求 root governance 文档包含以下精确历史短语的断言：

```text
Dream Geometry V2 Route Lock
```

不得以在 root docs 恢复该短语来使测试通过。

### 新测试语义

保留文件名，但将相关 test 的名称、docstring、assertion message 改为当前语义，例如：

```text
test_required_v2_canonical_documents_exist_and_governance_prioritizes_v2
```

它必须验证：

```text
1. protocol/v2/LAYER_CONSTITUTION.md 存在；
2. protocol/v2/CONSTITUTION.md 存在；
3. protocol/v2/LAYER_CONSTITUTION.md 明确：
   - “V2 is the only active architecture”；
   - L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0；
   - Capture / Admission / Assembly 是业务路径而非产品层；
4. protocol/v2/LEGACY_BOUNDARY.md 明确：
   - V1 / MT1 / pre-V2 prototype 是 retired history；
   - legacy source 暂时存在不等于活动 API；
   - V2 Core 不得 import legacy / terminal；
5. root README / ARCHITECTURE / ROADMAP / AGENTS
   不包含 “Dream Geometry V2 Route Lock”；
6. 该测试不得要求 V1 route lock、V1 tool table、nollm.cli、
   examples/openclaw 或任何 legacy command 作为活动治理证据。
```

该测试仍然要严格验证 V2 priority；只是将优先权锁定在真正的 L0 canonical documents，而不是旧 root wording。

---

## 5.2 `test_dg7_runtime_boundaries.py`

### 被替代的旧断言

删除／替换任何要求：

```text
ROADMAP.md 包含 DG5 / DG6 / DG7 的旧 delivery / roadmap fact sentence
```

root ROADMAP 不再是 sealed validation history 的数据库。

### 新测试语义

保留文件名，但将相关 test 的名称、docstring、assertion message 改为当前语义，例如：

```text
test_dg5_dg6_dg7_are_classified_in_component_progress_not_as_runtime
```

它必须读取：

```text
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
```

并验证其中明确且非歧义地记录：

```text
DG5:
  sealed / validation；
  evidence-preserving trace compaction；
  不替代原始证据或事实。

DG6:
  sealed / validation；
  isolated verification-only snapshot-compaction projection；
  不进入 core recall 或事实路径。

DG7:
  sealed / validation；
  explicit reference-runtime positive verification；
  不等于 production runtime、daemon、network service 或 terminal integration。
```

若当前 progress table 的表述不够明确，可仅在该文件补足上述分类；不得将旧 DG5/DG6/DG7 交付句重新放入 `ROADMAP.md`。

该测试还必须验证 root ROADMAP：

```text
- 只描述当前由 V2L0 收束到后续 adapter/integration 的路线；
- 不把 DG7 reference runtime 宣称为 production runtime；
- 不把 DG6 projection 宣称为 core recall。
```

---

## 5.3 `test_geometry.py`

### 被替代的旧断言

删除／替换任何要求：

```text
AGENTS.md 包含 D1 pure-polygon-overlap 边界句
```

`AGENTS.md` 是执行纪律和验证入口，不是 DG1 geometry contract 的 canonical owner。

### 新测试语义

保留文件名，但将相应测试名称、docstring、assertion message 改为当前语义，例如：

```text
test_v2_geometry_policy_is_pure_deterministic_and_terminal_independent
```

它必须读取：

```text
protocol/v2/LAYER_CONSTITUTION.md
protocol/v2/MODULE_DEPENDENCY_RULES.md
```

并验证：

```text
1. DG1 Geometry Kernel 属于 L2 Deterministic Domain Services；
2. DG1 的职责是 structured geometric computation：
   local charts, regular-hex / axial transforms,
   coverage-kernel / overlap / residual diagnostics；
3. DG1 不做：
   - natural-language understanding；
   - Evidence write / mutation；
   - fact or trust determination；
   - candidate discovery；
   - promotion decision；
   - admission placement invention；
   - recall ranking；
   - adapter / terminal / OpenClaw import；
4. geometry constrains placement and reading;
   geometry does not replace fact；
5. AGENTS.md 不再承担 D1 polygon-overlap wording 的 canonical contract。
```

如 `LAYER_CONSTITUTION.md` 尚未清晰写出第 2、3、4 点，可在该文件增补**概念性、非算法性**分层边界。不得修改 DG1 源码、DG1 sealed protocol、DG1 tests 或算法。

此迁移不得把 “pure deterministic geometry” 误写为“只允许 polygon overlap 一种唯一算法”。当前 DG1 的封板能力包括 local chart、hex transform、coverage kernel、phase/residual 等；C2 要保护的是“纯确定性且不越界”，不是重新把 DG1 缩回 pre-V2 D1 prototype。

---

## 6. Cross-test consistency sweep

在改动后、fixed gate 前，执行只读检查：

```powershell
rg -n `
  -e "Dream Geometry V2 Route Lock" `
  -e "Nollm V1 Route Lock" `
  -e "Stable historical V1 tool actions" `
  -e "nollm\.cli" `
  -e "examples/openclaw" `
  -e "D1 pure.*polygon.*overlap" `
  reference/python/tests README.md ARCHITECTURE.md ROADMAP.md AGENTS.md protocol/v2 docs
```

对所有命中逐一人工分类：

```text
允许：
  - 历史记录中明确标为 retired / migration / historical 的非操作性说明；
  - 新测试对 banned root wording 的负向断言；
  - Git history / taskbook 名称的历史引用。

不允许：
  - 任何 root document 把上述词作为当前操作指令；
  - 任一测试仍要求 root docs 包含 V1 route-lock、V1 CLI、
    examples/openclaw 或 D1 historical wording；
  - 任一文档将 DG7 写为 production runtime。
```

若发现额外测试在 root docs 上强制类似旧语义，而该测试不在 allowlist：

```text
停止并报告；
不得修改；
不得通过恢复旧 root 文本暂时掩盖。
```

---

## 7. 进度表与交付文档的最小更新

更新下列文档，仅使它们反映本任务已知事实：

```text
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/delivery/V2L0_DELIVERY_REPORT.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md
```

必须准确写明：

```text
- V2L0-C1R candidate 头为 242bf0d...；
- C1R fixed gate 38 passed、public V2 regression 109 passed是 pre-C2 evidence，
  不是 final C2 evidence；
- C2 的 final evidence 必须以 final head、fresh fixed gate、fresh public regression、
  fresh matrix、fresh capsule 为准；
- HAG1-C1R 是 accepted / unpromoted L5 File Admission Adapter；
- V2L0 仍为 candidate，直到 C2 接受审计；
- local main 仍以运行时检查为准，不得从 bundle remote ref 推断。
```

将本任务书逐字复制为：

```text
docs/delivery/NOLLM_V2L0_C2_MATRIX_LEGACY_GOVERNANCE_TEST_MIGRATION_AND_EVIDENCE_CLOSURE_TASK_20260707.md
```

此前已经提交的 V2L0、C1、C1R taskbooks 不得修改、删除或重写。

---

## 8. 固定门禁与原始日志

设置：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"
```

### 8.1 V2L0-C2 fixed gate

运行：

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

### 8.3 原始日志

两个门禁均必须在 final evidence build 前保存为真实 raw log：

```text
v2l0_c2_fixed_gate_raw.txt
v2l0_c2_public_v2_regression_raw.txt
```

每份原始日志必须包含：

```text
- exact invocation；
- PYTHONDONTWRITEBYTECODE、PYTEST_DISABLE_PLUGIN_AUTOLOAD、PYTHONPATH；
- start/end RFC3339 timestamps；
- 原始 stdout/stderr；
- 实际 process exit code；
- 不得用人工摘要替换。
```

任一 fixed gate / public regression 出现真实失败、timeout 或外部环境上限中断时：

```text
立即停止；
不得提交；
不得将 TQ1 matrix 结果当作固定门禁的替代。
```

---

## 9. Commit、fresh final matrix、evidence capsule 与单 bundle

### 9.1 Commit

仅在第 8 节两个门禁完整通过后：

```powershell
git diff --check
git add -- <allowed paths only>
git commit -m "test(v2): migrate legacy governance locks to canonical boundaries"
$finalHead = git rev-parse HEAD
git status --short
```

### 9.2 Fresh final-head TQ1 C7R matrix

```powershell
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$finalHead\v2l0-c2"
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

每个 `$*Exit` 必须独立检查。任一非零时：

```text
立即停止；
不得 build evidence；
不得 bundle；
不得改写任何 receipt；
不得通过修改矩阵输入或缩小 collection 规避失败。
```

最终 matrix 必须满足：

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

使用现有 sealed packager，不得修改其代码。将真实日志填入既有 slots：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py build-ref `
  --repo-root . `
  --receipt-root $receiptRoot `
  --final-head $finalHead `
  --final-verify-log matrix_verify_raw.txt `
  --governance-file <existing TQ1-C7R governance task> `
  --log "00_environment_and_git_state.txt=environment_git_raw.txt" `
  --log "01_rc_gate_pytest.txt=v2l0_c2_fixed_gate_raw.txt" `
  --log "04_dx1_dg0_dg6_targeted_gate.txt=v2l0_c2_public_v2_regression_raw.txt" `
  --log "05_matrix_plan.txt=matrix_plan_raw.txt" `
  --log "06_matrix_run_all.txt=matrix_run_all_raw.txt" `
  --log "07_matrix_verify.txt=matrix_verify_raw.txt" `
  --log "08_bundle_build_and_audit.txt=bundle_audit_raw.txt" `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead"
```

slot 文件名是 sealed packager 的历史布局；每个实际内容首行必须诚实标注保存的 V2L0-C2 command。

以下文字不得出现在 supplied slots：

```text
not produced for this local regression capsule
placeholder
synthetic result
```

fresh checkout 中：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref `
  --repo-root . `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead" `
  --expected-head $finalHead
```

并验证：

```text
- C2 taskbook 在 normal code tree；
- final evidence head 与 final Git head 精确相同；
- fixed gate、public regression、matrix plan/run/verify slots 均为实际原始输出；
- supplied slots 不含 placeholder；
- root docs 没有恢复 V1 操作导航；
- DG0/DG7/DG1 test 的 current canonical assertions 真实存在。
```

### 9.4 Single bundle

```powershell
$bundle = "C:\Users\chaos\nollm_v2l0_c2_canonical_governance_boundary_evidence_closure_20260707_<short-head>.bundle"

git bundle create $bundle --all
git bundle verify $bundle
git fsck --full
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
Get-FileHash $bundle -Algorithm SHA256
git status --short
```

bundle 必须包含：

```text
- V2L0 branch；
- 完整可达历史；
- final-head parentless evidence ref；
- V2L0、C1、C1R、C2 四份 taskbook 的 normal code history；
- 无未提交修改。
```

不得 main promotion，不得 push。

---

## 10. 停止条件

出现任一项必须立即停止并报告：

```text
- local main 不是 8bb324a...；
- current branch 不正确；
- 242bf0d... 不可达或工作树不 clean；
- 需要修改任何 sealed production module、HCG/HAG/HX/CX2 专属 test、TQ1 tool 或 package identity；
- 需要修改任何 allowlist 外路径；
- 需要删除、移动或重命名旧 source/test/docs/examples；
- 发现额外 root-doc legacy assertion test 而它不在 allowlist；
- fixed gate 或 public regression 出现真实 failure、timeout、环境时限中断；
- final matrix 非零；
- fresh evidence semantic verify 失败；
- 需要 HAG branch/evidence 改动；
- 需要远程操作、runtime activation 或子代理。
```

---

## 11. 完成后的准确表述

V2L0-C2 完成后仅表示：

> Nollm 的完整测试矩阵不再要求 root-level legacy wording 来证明 V2 priority、DG5/DG6/DG7 验证状态或 DG1 纯几何边界；这些事实现由各自的 V2 canonical constitution、component progress 与 protocol boundary 文档承担。V1/MT1/prototype 仍物理存在但已退役；OpenClaw 仍是冻结的 L5/L6 migration asset。V2L0-C2 不修改 Core、不删除历史源、不激活 runtime、不合并或提升 HAG、也不移动 main。

不得表述：

```text
V1 source 已删除；
OpenClaw 已接入；
HAG 已合并或已 main；
automatic admission 已启用；
global recall 已存在；
任何 terminal 可绕过 HX1；
main 已移动。
```
