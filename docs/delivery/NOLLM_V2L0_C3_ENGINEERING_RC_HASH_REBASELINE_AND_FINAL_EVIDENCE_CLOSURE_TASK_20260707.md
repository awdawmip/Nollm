# Nollm V2L0-C3：历史 Engineering RC 哈希重基线与最终证据闭合任务书

**日期**：2026-07-07
**阶段**：V2L0-C3 — Historical Engineering RC Hash Rebaseline / Final Evidence Closure
**当前 V2L0-C2 候选头**：`beb7f50c3272f768437a0952f9231150a1168cbe`
**活动开发基线**：`8bb324a3a5de46bebb6eadd217820627a971e2a0`
**已接受、未提升组件**：HAG1-C1R `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`
**继续分支**：`codex/v2l0-layer-constitution-source-reclassification`
**执行主体**：单一执行主体；禁止子代理、并行代理和后台任务。
**交付**：一个 complete-history Git bundle + 精确绑定 final head 的 parentless TQ1 evidence capsule。
**本任务不做**：不删除/移动 V1、MT1、OpenClaw、旧 Dream/Gravity source；不修改 Core、Workflow、Bridge、HCG、HAG 或 TQ1 工具；不激活 runtime；不提升 main；不执行 fetch/pull/push。

---

## 0. 本轮唯一问题与唯一处理方式

V2L0-C2 已形成干净候选提交 `beb7f50c...`，并真实通过：

```text
C2 fixed gate: 83 passed, 24 subtests passed
public V2 regression: 109 passed
```

但 fresh final-head TQ1 matrix 的 shard `s007` 非零，原因集中为：

```text
hash_manifest_sha256_mismatch:reference/python/tests/test_geometry.py
hash_manifest_size_mismatch:reference/python/tests/test_geometry.py
```

C2 对 `reference/python/tests/test_geometry.py` 的修改是经过授权且必要的：它将旧 root-level D1 wording lock 改为对 V2 canonical geometry boundary 的断言。

同时，旧 Engineering Gravity RC export manifest 把 `test_geometry.py` 列为受管辖 release artifact，RC hash manifest 也对其 canonical bytes 作 exact integrity 验证。因此，这是一次**已授权工件正文变更后未同步刷新历史 RC hash manifest**的保护性失败。

本任务只做一件事：

> 以现有 deterministic canonical-byte generator 重建 Engineering RC hash manifest，并证明只有 `reference/python/tests/test_geometry.py` 的 `size_bytes` / `sha256` 条目发生变化；随后重新执行 C2 gates、完整 final-head matrix 与 evidence capsule。

这不是：

```text
- 将旧 Engineering Gravity RC 重新设为活动架构；
- 恢复旧 V1 / D1 / root-document wording；
- 修改 Engineering RC 的 hash 规则、archive 算法、测试逻辑或 release manifest 路径；
- 放宽或跳过 RC artifact integrity tests；
- 删除 RC tests 以缩小 TQ1 collection；
- 修改 V2 Core；
- 接入 OpenClaw；
- 合并 HAG；
- main promotion。
```

在 V2L0/U2 后续物理清理前，Engineering RC suite 仍属于完整矩阵的历史测试输入；它的哈希完整性必须真实闭合，但不因此恢复为 V2 的活动产品路线。

---

## 1. 强制开始检查

在仓库根目录执行：

```powershell
git switch codex/v2l0-layer-constitution-source-reclassification
git status --short
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git merge-base --is-ancestor beb7f50c3272f768437a0952f9231150a1168cbe HEAD
git diff --check
git log --oneline --decorate -10
```

开始条件：

```text
- 当前分支必须为 codex/v2l0-layer-constitution-source-reclassification；
- current HEAD 必须精确为 beb7f50c3272f768437a0952f9231150a1168cbe，
  或 beb7f50c... 必须是 current HEAD 的祖先且其后没有非本任务提交；
- local main 必须精确为 8bb324a3a5de46bebb6eadd217820627a971e2a0；
- tracked worktree 必须 clean；
- 未发生 fetch / pull / push；
- HAG branch 与 refs/nollm-delivery/tq1-c7r/0e0d21... 不得改写；
- 不得 reset / rebase / squash / cherry-pick / merge；
- 不得创建平行 C3 分支；
- 不得 main promotion。
```

任一条件不成立时，立即停止并报告 exact refs / status；不得修复、清理或猜测。

---

## 2. Sealed baseline 与禁止事项

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
- 修改 reference/python/nollm/engineering_rc_export.py；
- 修改 reference/python/nollm/engineering_rc_archive.py；
- 修改 reference/python/nollm/engineering_rc_final_smoke.py；
- 修改 reference/python/scripts/check_engineering_rc_export.py；
- 修改 reference/python/scripts/build_engineering_rc_export_archive.py；
- 修改任何 engineering_rc / archive / export test；
- 修改 TQ1 runner、packager、verifier；
- 修改 pyproject / package identity；
- 修改 C2 已迁移的三份 legacy-governance tests；
- 恢复 README / ARCHITECTURE / ROADMAP / AGENTS 中的 V1 route lock、
  V1 tool action table、nollm.cli 或 examples/openclaw 操作导航；
- 删除、移动或重命名任何 legacy source/test/example/docs；
- 将旧 Engineering RC 写成当前 V2 runtime 或活动产品路线；
- OpenClaw/runtime/network/daemon/database/cache/LLM/NLP/embedding/semantic search activation；
- main promotion；
- 任何远程 Git 操作；
- 子代理。
```

---

## 3. 唯一允许修改路径

仅允许修改或新增：

```text
docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json

docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/delivery/V2L0_DELIVERY_REPORT.md
docs/delivery/NOLLM_V2L0_C3_ENGINEERING_RC_HASH_REBASELINE_AND_FINAL_EVIDENCE_CLOSURE_TASK_20260707.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md
```

注意：

```text
- `docs/releases/...ARTIFACT_HASHES...json` 是唯一被允许修改的 Engineering RC 文件；
- 它必须由 existing script deterministic rewrite，禁止手工编辑；
- 若 deterministic rewrite 试图改动任何其他 tracked file，立即停止；
- 若任何 allowlist 外路径需要修改，立即停止并报告。
```

---

## 4. 重基线前的精确失败证明

设置环境：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"
```

从 repo root 运行 export checker，并保存完整原始输出：

```powershell
$beforeLog = Join-Path $env:TEMP "v2l0_c3_rc_hash_before_raw.txt"
$startedAt = [DateTimeOffset]::UtcNow.ToString("o")

@(
  "V2L0-C3 Engineering RC pre-rebaseline checker",
  "started_at=$startedAt",
  "command=python reference/python/scripts/check_engineering_rc_export.py --repo-root .",
  "PYTHONDONTWRITEBYTECODE=$env:PYTHONDONTWRITEBYTECODE",
  "PYTEST_DISABLE_PLUGIN_AUTOLOAD=$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD",
  "PYTHONPATH=$env:PYTHONPATH"
) | Set-Content -Path $beforeLog -Encoding utf8

python reference/python/scripts/check_engineering_rc_export.py --repo-root . *>> $beforeLog
$beforeExit = $LASTEXITCODE

@(
  "ended_at=$([DateTimeOffset]::UtcNow.ToString("o"))",
  "exit_code=$beforeExit"
) | Add-Content -Path $beforeLog -Encoding utf8
```

`$beforeExit` 必须为 `1`，且 JSON report 的失败集合必须**精确等于**：

```text
hash_manifest_sha256_mismatch:reference/python/tests/test_geometry.py
hash_manifest_size_mismatch:reference/python/tests/test_geometry.py
```

不得存在：

```text
missing_path
invalid_manifest
artifact count / sort mismatch
任何其他 artifact path mismatch
任何 release/export semantic failure
```

用下面临时验证脚本确认。该脚本只写入 `$env:TEMP`，不得写入 repo：

```powershell
$assertBefore = Join-Path $env:TEMP "assert_v2l0_c3_before.py"

@'
import json
import pathlib
import sys

log_path = pathlib.Path(sys.argv[1])
text = log_path.read_text(encoding="utf-8")
start = text.find("{")
end = text.rfind("}")
if start < 0 or end < start:
    raise SystemExit("C3_PRECHECK_NO_JSON_REPORT")
report = json.loads(text[start:end + 1])
expected = {
    "hash_manifest_sha256_mismatch:reference/python/tests/test_geometry.py",
    "hash_manifest_size_mismatch:reference/python/tests/test_geometry.py",
}
actual = set(report.get("failures", []))
if actual != expected:
    raise SystemExit(
        "C3_PRECHECK_UNEXPECTED_FAILURES:"
        + json.dumps(sorted(actual), ensure_ascii=False)
    )
if report.get("ok") is not False:
    raise SystemExit("C3_PRECHECK_EXPECTED_FAILURE_NOT_OBSERVED")
print("C3_PRECHECK_EXACT_EXPECTED_MISMATCH_OK")
'@ | Set-Content -Path $assertBefore -Encoding utf8

python $assertBefore $beforeLog
if ($LASTEXITCODE -ne 0) {
  throw "C3 pre-rebaseline mismatch proof failed."
}
```

若此证明不成立，立即停止；不得运行 `--write-hashes`。

---

## 5. 唯一允许的 RC manifest 重建

### 5.1 先记录 HEAD manifest

把 current committed manifest 保存到 `$env:TEMP`：

```powershell
$manifestPath = "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json"
$oldManifest = Join-Path $env:TEMP "v2l0_c3_rc_hash_manifest_before.json"

git show "HEAD:$manifestPath" | Set-Content -Path $oldManifest -Encoding utf8
if ($LASTEXITCODE -ne 0) {
  throw "Unable to export committed RC hash manifest."
}
```

### 5.2 只能调用现有 writer

运行：

```powershell
$rebuildLog = Join-Path $env:TEMP "v2l0_c3_rc_hash_rebuild_raw.txt"

@(
  "V2L0-C3 deterministic RC hash manifest rebuild",
  "started_at=$([DateTimeOffset]::UtcNow.ToString("o"))",
  "command=python reference/python/scripts/check_engineering_rc_export.py --repo-root . --write-hashes",
  "PYTHONDONTWRITEBYTECODE=$env:PYTHONDONTWRITEBYTECODE",
  "PYTEST_DISABLE_PLUGIN_AUTOLOAD=$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD",
  "PYTHONPATH=$env:PYTHONPATH"
) | Set-Content -Path $rebuildLog -Encoding utf8

python reference/python/scripts/check_engineering_rc_export.py --repo-root . --write-hashes *>> $rebuildLog
$rebuildExit = $LASTEXITCODE

@(
  "ended_at=$([DateTimeOffset]::UtcNow.ToString("o"))",
  "exit_code=$rebuildExit"
) | Add-Content -Path $rebuildLog -Encoding utf8

if ($rebuildExit -ne 0) {
  throw "Deterministic RC manifest rebuild failed."
}
```

此步骤后，暂时只允许一个 tracked diff：

```text
docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json
```

执行：

```powershell
git diff --name-only
git diff --check
git status --short
```

若出现任何其他 tracked path，立即停止，不得清理或手工修复。

### 5.3 强制证明：仅一个 artifact record 的两个字段变化

用以下临时检查脚本验证：

```powershell
$assertAfter = Join-Path $env:TEMP "assert_v2l0_c3_after.py"

@'
import hashlib
import json
import pathlib
import sys

repo = pathlib.Path(".").resolve()
before_path = pathlib.Path(sys.argv[1])
manifest_path = repo / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json"

before = json.loads(before_path.read_text(encoding="utf-8"))
after = json.loads(manifest_path.read_text(encoding="utf-8"))

for key in ("schema", "date", "status", "claim", "source_manifest", "excluded_local_paths", "artifact_count"):
    if before.get(key) != after.get(key):
        raise SystemExit(f"C3_HEADER_CHANGED:{key}")

before_items = before.get("artifacts")
after_items = after.get("artifacts")
if not isinstance(before_items, list) or not isinstance(after_items, list):
    raise SystemExit("C3_ARTIFACTS_NOT_LIST")
if [x.get("path") for x in before_items] != [x.get("path") for x in after_items]:
    raise SystemExit("C3_ARTIFACT_PATH_LIST_CHANGED")

before_by_path = {x["path"]: x for x in before_items}
after_by_path = {x["path"]: x for x in after_items}
changed = [
    path for path in before_by_path
    if before_by_path[path] != after_by_path[path]
]
expected_path = "reference/python/tests/test_geometry.py"
if changed != [expected_path]:
    raise SystemExit("C3_UNEXPECTED_ARTIFACT_RECORD_CHANGES:" + json.dumps(changed))

before_record = before_by_path[expected_path]
after_record = after_by_path[expected_path]
if set(before_record) != {"path", "size_bytes", "sha256"}:
    raise SystemExit("C3_UNEXPECTED_BEFORE_RECORD_SCHEMA")
if set(after_record) != {"path", "size_bytes", "sha256"}:
    raise SystemExit("C3_UNEXPECTED_AFTER_RECORD_SCHEMA")
if before_record["path"] != expected_path or after_record["path"] != expected_path:
    raise SystemExit("C3_WRONG_CHANGED_PATH")

target = repo / expected_path
data = target.read_bytes().replace(b"\r\n", b"\n")
if b"\r" in data:
    raise SystemExit("C3_BARE_CR_IN_TEST_GEOMETRY")
if after_record["size_bytes"] != len(data):
    raise SystemExit("C3_SIZE_NOT_CURRENT_CANONICAL_BYTES")
if after_record["sha256"] != hashlib.sha256(data).hexdigest():
    raise SystemExit("C3_SHA_NOT_CURRENT_CANONICAL_BYTES")

print("C3_SINGLE_ARTIFACT_REBASELINE_OK")
print("old_size=", before_record["size_bytes"])
print("new_size=", after_record["size_bytes"])
print("old_sha256=", before_record["sha256"])
print("new_sha256=", after_record["sha256"])
'@ | Set-Content -Path $assertAfter -Encoding utf8

python $assertAfter $oldManifest
if ($LASTEXITCODE -ne 0) {
  throw "RC manifest rebaseline changed more than the authorized test_geometry record."
}
```

禁止：

```text
- 手工编辑 JSON；
- 修改 artifact list；
- 修改 artifact_count；
- 修改 release manifest / evaluation guide / archive code；
- 同时更新任意其他 hash；
- 以“历史文件过时”为由跳过或删除 RC integrity tests。
```

---

## 6. 文档与任务书记录

只在完成第 5 节的单条目证明后，更新以下 allowed docs：

```text
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md
docs/delivery/V2L0_DELIVERY_REPORT.md
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md
```

必须准确表达：

```text
- C2 candidate head 为 beb7f50c...；
- C2 已完成 legacy-governance test migration，但没有 final evidence；
- C3 只重基线旧 Engineering RC manifest 中 test_geometry.py 的 canonical hash；
- 此重基线是因为完整 TQ1 仍收集该 historical RC artifact integrity suite；
- 不改变 V1/MT1/prototype retired classification；
- 不将 Engineering RC 设为 current V2 runtime；
- HAG1-C1R 仍是 accepted / unpromoted；
- V2L0 仍是 candidate，直至 C3 evidence 和接受审计完成；
- local main 状态必须在实际机器重新核验。
```

将本任务书逐字复制到：

```text
docs/delivery/NOLLM_V2L0_C3_ENGINEERING_RC_HASH_REBASELINE_AND_FINAL_EVIDENCE_CLOSURE_TASK_20260707.md
```

此前已提交的 V2L0、C1、C1R、C2 taskbooks 不得修改或删除。

---

## 7. 固定门禁与真实原始日志

### 7.1 Engineering RC focused integrity gate

先运行：

```powershell
python -m pytest -q `
  reference/python/tests/test_engineering_rc_artifact_hashes.py `
  reference/python/tests/test_engineering_rc_export.py `
  reference/python/tests/test_engineering_rc_archive.py `
  reference/python/tests/test_engineering_rc_final_smoke.py
```

保存为：

```text
v2l0_c3_engineering_rc_integrity_raw.txt
```

该 gate 必须完整通过。它证明：

```text
- manifest 与现有 source exact match；
- export checker 正常；
- deterministic archive 正常；
- RC final smoke unit contract 不被破坏。
```

### 7.2 Final V2L0-C3 fixed gate

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

保存为：

```text
v2l0_c3_fixed_gate_raw.txt
```

### 7.3 Final public V2 regression

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

保存为：

```text
v2l0_c3_public_v2_regression_raw.txt
```

### 7.4 统一原始日志格式

三份 gate raw logs 均必须包含：

```text
- exact invocation；
- PYTHONDONTWRITEBYTECODE、PYTEST_DISABLE_PLUGIN_AUTOLOAD、PYTHONPATH；
- start/end RFC3339 timestamps；
- original stdout/stderr；
- actual exit code；
- 不得以手工摘要替代。
```

任一 gate 出现真实 failure、timeout 或外部环境上限中断时：

```text
立即停止；
不得提交；
不得启动 TQ1 matrix；
不得用 matrix 结果替代 fixed gate。
```

---

## 8. Commit、fresh final matrix、capsule 与单 bundle

### 8.1 Commit

仅在第 5、7 节完整通过后：

```powershell
git diff --check
git add -- `
  docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json `
  docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md `
  docs/validation/V2L0_LAYER_CONSTITUTION_VALIDATION_REPORT.md `
  docs/delivery/V2L0_DELIVERY_REPORT.md `
  docs/delivery/NOLLM_V2L0_C3_ENGINEERING_RC_HASH_REBASELINE_AND_FINAL_EVIDENCE_CLOSURE_TASK_20260707.md `
  validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md

git commit -m "chore(rc): rebaseline historical RC artifact hash after V2 governance migration"
$finalHead = git rev-parse HEAD
git status --short
```

`git status --short` 必须为空。

### 8.2 Fresh final-head matrix

```powershell
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$finalHead\v2l0-c3"
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

逐项检查 `$planExit`、`$runExit`、`$verifyExit`。任一非零：

```text
立即停止；
不得 build evidence；
不得 bundle；
不得覆盖 receipt；
不得改变 matrix collection 或 timeout contract 规避失败。
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

### 8.3 Parentless evidence capsule

使用现有 sealed packager，不得修改其代码。

先生成真实 `environment_git_raw.txt`，包括：

```text
finalHead
git status --short
git diff --check
git fsck --full
git rev-parse main
git rev-parse origin/main
current branch
```

`08_bundle_build_and_audit.txt` 是 sealed packager 的历史 slot 名。由于 final bundle 不可能在自己的 evidence capsule 内完成自引用审计，其内容必须是**真实 pre-bundle repository audit**，而不是 placeholder，并在首行明确：

```text
V2L0-C3 pre-bundle repository audit;
final transport bundle verify/SHA are recorded outside the capsule by the delivery/acceptance audit.
```

该 log 至少包含：

```text
git status --short
git diff --check
git fsck --full
git bundle list-heads <not applicable before creation>  # 不得伪造输出
```

不得写：

```text
not produced for this local regression capsule
placeholder
synthetic result
final bundle verified
```

然后：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py build-ref `
  --repo-root . `
  --receipt-root $receiptRoot `
  --final-head $finalHead `
  --final-verify-log matrix_verify_raw.txt `
  --governance-file <existing TQ1-C7R governance task> `
  --log "00_environment_and_git_state.txt=environment_git_raw.txt" `
  --log "01_rc_gate_pytest.txt=v2l0_c3_fixed_gate_raw.txt" `
  --log "04_dx1_dg0_dg6_targeted_gate.txt=v2l0_c3_public_v2_regression_raw.txt" `
  --log "05_matrix_plan.txt=matrix_plan_raw.txt" `
  --log "06_matrix_run_all.txt=matrix_run_all_raw.txt" `
  --log "07_matrix_verify.txt=matrix_verify_raw.txt" `
  --log "08_bundle_build_and_audit.txt=pre_bundle_repository_audit_raw.txt" `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead"
```

**附加 RC focused gate 证据**：若 packager 支持额外 `--log` name，加入：

```text
09_v2l0_c3_engineering_rc_integrity_gate.txt=v2l0_c3_engineering_rc_integrity_raw.txt
```

若 packager 不支持额外 slot，不得修改 packager；应把 focused-gate raw log 的 SHA-256、命令和结果精确记录进 `V2L0_FIXED_GATE_RECEIPT.md`，并保留原文件作为 external delivery audit artifact。

Fresh checkout verify：

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref `
  --repo-root . `
  --evidence-ref "refs/nollm-delivery/tq1-c7r/$finalHead" `
  --expected-head $finalHead
```

还必须人工验证：

```text
- final evidence ref 指向 finalHead；
- filled slots 是实际原始输出；
- 无 supplied placeholder；
- RC manifest 只重基线 test_geometry record；
- root docs 没有恢复 V1 navigation；
- C3 taskbook 在 normal code tree。
```

### 8.4 One complete-history Git bundle

完成 capsule verify 后：

```powershell
$bundle = "C:\Users\chaos\nollm_v2l0_c3_engineering_rc_hash_rebaseline_evidence_closure_20260707_<short-head>.bundle"

git bundle create $bundle --all
git bundle verify $bundle
git fsck --full
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
Get-FileHash $bundle -Algorithm SHA256
git status --short
```

最终 bundle 必须包含：

```text
- V2L0 branch；
- 完整可达历史；
- final-head parentless evidence ref；
- V2L0、C1、C1R、C2、C3 五份 taskbook 的 normal code history；
- 无未提交变更。
```

不得 main promotion，不得 push。

---

## 9. 停止条件

出现任一项立即停止并报告：

```text
- local main 不是 8bb324a...；
- HEAD / branch 不符合第 1 节；
- tracked worktree 不 clean；
- pre-rebaseline checker 的 failures 不精确等于 test_geometry 的两项 hash mismatch；
- --write-hashes 改动了 allowlist 外文件；
- manifest comparison 显示除 test_geometry 外任何 artifact record、路径列表、header 或 artifact_count 改变；
- 需要修改任何 source code、RC test、release guide、export manifest、archive manifest 或 TQ1 tool；
- focused integrity gate / V2L0 gate / public V2 regression 有 failure、timeout 或环境时限中断；
- final matrix 非零；
- evidence semantic verify 失败；
- HAG branch/evidence 需要改变；
- 需要 remote operation、runtime activation 或子代理。
```

---

## 10. 完成后的准确表述

V2L0-C3 完成后仅可表述：

> V2L0 已将活动导航与完整矩阵的历史治理测试迁移到 V2 canonical documents；由于 `test_geometry.py` 是旧 Engineering RC artifact manifest 中仍受完整矩阵核验的历史文件，C3 对其进行一次受限、可证明只影响单条 artifact record 的 canonical hash 重基线。此举维持历史测试输入的完整性，不改变其 retired classification，不恢复 V1 操作入口，不修改 Core，不激活 runtime，不合并或提升 HAG，也不移动 main。

不得表述：

```text
旧 Engineering RC 已重新成为活动 V2 runtime；
V1 source 已被删除；
OpenClaw 已接入；
HAG 已合并/main；
自动 admission / global recall 已启用；
任何 terminal 可绕过 HX1；
main 已移动。
```
