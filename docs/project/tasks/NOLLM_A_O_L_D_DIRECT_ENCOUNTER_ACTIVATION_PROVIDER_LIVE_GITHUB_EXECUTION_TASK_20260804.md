# Nollm A-O-L-D：Direct Encounter Activation、Provider Live 与 GitHub 连续交付任务书

**任务文件名**：`NOLLM_A_O_L_D_DIRECT_ENCOUNTER_ACTIVATION_PROVIDER_LIVE_GITHUB_EXECUTION_TASK_20260804.md`
**日期**：2026-08-04
**受影响模块**：`A=ACCESS | O=OPENCLAW | L=LAB | D=DISTRIBUTIONS`
**回归模块**：`CORE | SNAPSHOT | TRACE | HISTORY | AUDIT`
**目标架构**：`NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md`
**活动路线**：`NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md`
**阶段代码提交**：`8182f98ffa13ddbc6bdaa788f97648c30666f236`
**阶段代码补丁**：`0001-feat-openclaw-render-direct-field-encounter-activation.patch`
**阶段完整历史 Bundle**：`nollm_v313r1_direct_activation_stage_20260804.bundle`
**GitHub 仓库**：`awdawmip/Nollm`
**建议短期分支**：`codex/aold-v313r1-direct-activation`
**主环境**：Windows 10/11、PowerShell 7、Git、GitHub CLI、Python、Node 24+、真实 OpenClaw Host/Provider
**AGENTS 约束**：仓库根目录 `AGENTS.md` 必须存在且严格为 0 bytes
**交付要求**：每个主要 Gate 提交并推送 GitHub；最终工作树 clean；仓库外生成并验证一个完整历史 Git Bundle
**环境受限原则**：无法执行的 Provider、Windows、Node 或 GitHub 项只能标记为 `ENVIRONMENT_BLOCKED`，留下完整命令、预期结果和恢复指引；不得补造通过结果

---

# 0. 可验证结果

```text
1. 以最新 origin/main 为动态基线，不回退到旧 Bundle；
2. 将 V3.13 Rev1 架构、路线和本任务登记为唯一活动依据；
3. 恢复非空、可复算的生命周期删除依据；
4. 生成唯一通用 MODULE_BOUNDARY_REPORT；
5. 在代码修改前记录当前 V3.12 Provider/Host baseline；
6. 应用或复核阶段提交 8182f98；
7. 直接使用 FieldEncounterResult 和 current Statement 生成隐藏文本；
8. 不新增 MODEL_ADAPTER、Packet、epoch、派生 cache 或额外 LLM；
9. 收敛重复 renderer；
10. 真实验证 query/write/mixed/restart/concurrency；
11. 测量读取、写入、Provider、本地渲染的 p50/p95/max；
12. 只删除真实 Live 已替代且 lifecycle=REMOVABLE 的旧路径；
13. 每个主要 Gate commit 并 push 到 GitHub；
14. 最终进入 main 或形成可合并 PR；
15. 生成完整历史 Git Bundle 和阶段报告。
```

---

# 1. 任务推进向量

```text
任务推进向量：
CORE 0% |
SNAPSHOT 0% |
TRACE 0% |
ACCESS +5% |
HISTORY 0% |
AUDIT 0% |
OPENCLAW +15% |
LAB +10% |
DISTRIBUTIONS +5%

主方向：
不再增加生产架构层；
复用 Unified Field Encounter 和现有 Statement/Recall；
完成真实 Provider 读写闭环；
收敛精确文本注入路径；
取得真实调用拓扑和时延；
持续推送 GitHub，避免长任务只存在本地。

范围变化：
撤回正式 MODEL_ADAPTER；
撤回 MemoryActivationPacket、scope epoch 和派生 cache；
神经 Adapter 仅保留为 PAUSED_RESEARCH。
```

每个 Gate 开始和结束复述：

```text
C0 | S0 | T0 | A+5 | H0 | U0 | O+15 | L+10 | D+5
```

并记录：

```text
实际修改模块；
是否修改 Core；
是否新增持久状态；
是否新增 Provider 调用；
是否恢复双 Recall/Placement；
是否出现第二语义 session；
是否删除未达 REMOVABLE 的文件；
AGENTS 是否仍 0 bytes；
GitHub push 是否成功；
实际偏差。
```

---

# 2. 任务前模块完成度

开工时必须从最新 Module Ledger 复核。规划基线：

| 模块 | 生命周期 | 当前完成度 | 置信度 | 已验证能力 | 当前缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | CAPABILITY_VALIDATED | 93% | 高 | 几何、Surface、Locality、原子状态 | 回归 | 0 |
| SNAPSHOT | IMPLEMENTED | 50% | 中高 | state bytes | 增量/version | 0 |
| TRACE | IMPLEMENTED | 40% | 中 | sink 隔离 | metrics | 0 |
| ACCESS | CAPABILITY_VALIDATED | 98% | 高 | Unified Encounter、conditional commit | Provider-scale direct activation | 是 |
| HISTORY | PROPOSED | 10% | 低 | 章程 | 暂停 | 0 |
| AUDIT | PROPOSED | 10% | 低 | 章程 | 暂停 | 0 |
| OPENCLAW | IMPLEMENTED | 98% | 中高 | one Wire、Writer、文本注入基础 | 真实 Live、重复 renderer | 是 |
| LAB | IMPLEMENTED | 99% | 中 | offline fixtures | Provider/latency 对照 | 是 |
| DISTRIBUTIONS | IMPLEMENTED | 99% | 中 | main/Manifest 基础 | authority/boundary/GitHub 真值 | 是 |

---

# 3. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计方向 | 本任务交付 | 验收 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 93 | 93 | 0 | 无变化 | full regression | multi-layer/Stitch |
| SNAPSHOT | 50 | 50 | 0 | 无变化 | tests | incremental |
| TRACE | 40 | 40 | 0 | 无变化 | tests | metrics |
| ACCESS | 98 | 99 | +5 向量 | direct current Statement projection | unit + live | scale |
| HISTORY | 10 | 10 | 0 | 无 | boundary | paused |
| AUDIT | 10 | 10 | 0 | 无 | boundary | paused |
| OPENCLAW | 98 | 99 | +15 向量 | real query/write/mixed + one renderer | live | multi-provider |
| LAB | 99 | 99 | +10 向量 | latency/call baseline | evidence | long experiments |
| DISTRIBUTIONS | 99 | 99 | +5 向量 | authority/boundary/GitHub delivery | manifest + refs | formal release |

99% 不是永久封版。

---

# 4. Codex 执行约定

## 4.1 必须从任务包读取

```text
NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md
NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md
NOLLM_V3_13_REV1_IMPLEMENTATION_STEPS_20260804.md
本任务书
V3_13_REV1_EXECUTION_REPORT_20260804.md
```

## 4.2 PowerShell 初始化

在 Codex PowerShell 中先执行：

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path ".").Path
$TaskPackRoot = "<TASKPACK_EXTRACTED_ROOT>"
$Branch = "codex/aold-v313r1-direct-activation"

$NollmRoot = Split-Path $RepoRoot -Parent
$ArtifactRoot = Join-Path $NollmRoot "artifacts"
$BundleRoot = Join-Path $NollmRoot "bundles"
$ArchiveRoot = Join-Path $NollmRoot "archives"

New-Item -ItemType Directory -Force `
  $ArtifactRoot, $BundleRoot, $ArchiveRoot | Out-Null

$env:NOLLM_ARTIFACT_ROOT = $ArtifactRoot
$env:NOLLM_BUNDLE_ROOT = $BundleRoot
$env:NOLLM_ARCHIVE_ROOT = $ArchiveRoot
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
```

禁止把 `<TASKPACK_EXTRACTED_ROOT>` 原样执行；必须替换为实际解压目录。

## 4.3 GitHub 前置

```powershell
git --version
gh --version
gh auth status
```

若 `gh auth status` 失败：

```powershell
gh auth login
gh auth status
```

GitHub 推送是本任务的正式 Gate。认证或网络不可用时：

```text
本地 commit 和 Bundle 继续完成；
push Gate 标记 ENVIRONMENT_BLOCKED；
保存命令、stderr、时间和恢复步骤；
不得宣称 GitHub 已推送。
```

---

# 5. Gate 0：动态基线与现场保全

## 5.1 同步最新 main

```powershell
git status -sb
if (git status --porcelain) {
  throw "Working tree is not clean. Preserve user changes before continuing."
}

git fetch origin --prune --tags
git switch main
git pull --ff-only origin main

$RepositoryHead = (git rev-parse HEAD).Trim()
$DefaultBranch = (gh repo view --json defaultBranchRef `
  --jq ".defaultBranchRef.name").Trim()

if ($DefaultBranch -ne "main") {
  throw "Unexpected default branch: $DefaultBranch"
}
```

## 5.2 建立短期分支

```powershell
if (git show-ref --verify --quiet "refs/heads/$Branch") {
  git switch $Branch
  git rebase origin/main
} else {
  git switch -c $Branch
}
```

禁止在 `main` 直接长期开发。

## 5.3 检查 AGENTS

```powershell
$Agents = Join-Path $RepoRoot "AGENTS.md"
if (-not (Test-Path $Agents)) {
  throw "AGENTS.md must exist."
}
if ((Get-Item $Agents).Length -ne 0) {
  throw "AGENTS.md must be exactly zero bytes."
}

$AgentsSha = (Get-FileHash $Agents -Algorithm SHA256).Hash.ToLowerInvariant()
if ($AgentsSha -ne "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") {
  throw "AGENTS.md empty-file SHA mismatch."
}

$AgentsBlob = (git hash-object AGENTS.md).Trim()
if ($AgentsBlob -ne "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391") {
  throw "AGENTS.md Git blob is not empty."
}
```

## 5.4 保存起点证据

```powershell
$StartRoot = Join-Path $ArtifactRoot "V3_13_REV1_START"
New-Item -ItemType Directory -Force $StartRoot | Out-Null

git status -sb | Set-Content `
  (Join-Path $StartRoot "git-status.txt") -Encoding utf8
git log --graph --decorate --oneline -n 100 | Set-Content `
  (Join-Path $StartRoot "git-log.txt") -Encoding utf8
git branch -a -vv | Set-Content `
  (Join-Path $StartRoot "git-branches.txt") -Encoding utf8
git worktree list --porcelain | Set-Content `
  (Join-Path $StartRoot "git-worktrees.txt") -Encoding utf8
git tag --list | Set-Content `
  (Join-Path $StartRoot "git-tags.txt") -Encoding utf8
git ls-remote --heads origin | Set-Content `
  (Join-Path $StartRoot "remote-heads.txt") -Encoding utf8
```

## 5.5 读取活动依据

```powershell
Get-Content `
  docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md

Get-Content `
  docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_12_UNIFIED_FIELD_ENCOUNTER_READ_WRITE_DUALITY_20260728.md

Get-Content `
  "$TaskPackRoot\NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md"

Get-Content `
  "$TaskPackRoot\NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md"

Get-Content docs/project/ACTIVE_PROJECT.md
Get-Content docs/project/NOLLM_CURRENT_STATUS.md
Get-Content docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

## 5.6 基础治理 Gate

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py

python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/MODULE_BOUNDARY_REPORT.json

python tools/check_active_tree_assets.py
```

若当前工具仍写旧任务特定报告：

```text
先保留运行结果；
在 Gate 1 中更新默认输出路径；
不得因为文件名旧而跳过边界检查。
```

### Gate 0 PASS

```text
latest origin/main 已记录；
working tree clean；
短期分支建立；
AGENTS=0 bytes；
Manifest/Boundary 可执行；
用户修改无损；
尚未删除生产或迁移资产。
```

---

# 6. Gate 1：活动权威与生命周期真值

## 6.1 复制活动架构和路线进入仓库

仅在项目文档策略允许当前活动架构进入 Git 时执行：

```powershell
Copy-Item `
  "$TaskPackRoot\NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md" `
  "docs/architecture/" -Force

Copy-Item `
  "$TaskPackRoot\NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md" `
  "docs/project/" -Force

Copy-Item `
  "$TaskPackRoot\NOLLM_A_O_L_D_DIRECT_ENCOUNTER_ACTIVATION_PROVIDER_LIVE_GITHUB_EXECUTION_TASK_20260804.md" `
  "docs/project/tasks/" -Force
```

更新：

```text
ACTIVE_PROJECT.md；
NOLLM_CURRENT_STATUS.md；
Module Ledger。
```

必须分别登记：

```text
repository HEAD；
task input HEAD；
latest capability HEAD；
latest Provider Live HEAD；
latest governance HEAD；
latest Bundle HEAD。
```

## 6.2 生命周期计划

若当前 `ACTIVE_ASSET_CURATION_PLAN.json/.csv` 为 0 bytes：

```text
不得依据它删除文件。
```

建立唯一 JSON 权威：

```text
docs/architecture/module-ownership/ACTIVE_ASSET_LIFECYCLE_PLAN.json
```

CSV 由工具生成：

```text
docs/architecture/module-ownership/ACTIVE_ASSET_LIFECYCLE_PLAN.csv
```

字段至少：

```text
path
owner
target_owner
current_importers
replacement
migration_capability
removal_conditions
validation
verified_head
lifecycle
```

只有 `REMOVABLE` 可删除。

## 6.3 通用 Boundary

更新工具，使默认报告为：

```text
docs/architecture/module-ownership/MODULE_BOUNDARY_REPORT.json
```

重新运行：

```powershell
python tools/generate_module_ownership_manifest.py --write
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py

python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/MODULE_BOUNDARY_REPORT.json

python tools/check_active_tree_assets.py
```

## 6.4 Checkpoint commit + GitHub push

```powershell
git add `
  docs/architecture `
  docs/project `
  tools `
  AGENTS.md

git diff --cached --check
git commit -m "docs(project): activate V3.13 Rev1 direct activation"

git push -u origin $Branch
```

如果没有实际变化，不创建空提交，但仍执行：

```powershell
git push -u origin $Branch
```

### Gate 1 PASS

```text
唯一活动架构；
唯一 Current task；
HEAD 层次清楚；
生命周期 JSON 非空；
通用 Boundary 唯一；
GitHub 已收到 checkpoint。
```

---

# 7. Gate 2：修改前 Provider/Host Baseline

## 7.1 环境探测

```powershell
node --version
npm --version
python --version

$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd"
if (-not (Test-Path $OpenClaw)) {
  $OpenClaw = (Get-Command openclaw.cmd -ErrorAction SilentlyContinue).Source
}
if (-not $OpenClaw -or -not (Test-Path $OpenClaw)) {
  throw "ENVIRONMENT_BLOCKED: OpenClaw command not found."
}

& $OpenClaw --version
& $OpenClaw plugins list --json
& $OpenClaw agents list --json
```

Node 必须满足 package `engines`。当前 Formation Loop 要求 Node 24+。

## 7.2 Python baseline

```powershell
$env:PYTHONPATH = @(
  "$RepoRoot\packages\nollm-core\src",
  "$RepoRoot\packages\nollm-snapshot\src",
  "$RepoRoot\packages\nollm-trace\src",
  "$RepoRoot\packages\nollm-access\src",
  "$RepoRoot\integrations\openclaw\formation-loop\python",
  "$RepoRoot\reference\python"
) -join ";"

python -m pytest -q `
  integrations/openclaw/formation-loop/tests/test_openclaw_field_encounter.py `
  integrations/openclaw/formation-loop/tests/test_memory_loop.py
```

## 7.3 Node baseline

```powershell
Push-Location integrations/openclaw/formation-loop
try {
  npm ci
  npm test
  npm run plugin:check
} finally {
  Pop-Location
}
```

若 npm registry、Node 版本或 OpenClaw 依赖不可用：

```text
记录为 ENVIRONMENT_BLOCKED；
保存 node/npm 版本、registry、stderr；
不改 package-lock；
继续可执行的 Python Gate。
```

## 7.4 安装独立 Live Profile

必须使用独立 Statement/Memory workspace，不覆盖旧数据：

```powershell
$LiveRoot = Join-Path $NollmRoot "workspaces\v313r1-provider-live"
$StatementWorkspace = Join-Path $LiveRoot "statements"
$MemoryWorkspace = Join-Path $LiveRoot "memory"
$CaptureScope = "v313r1-provider-live"

New-Item -ItemType Directory -Force `
  $StatementWorkspace, $MemoryWorkspace | Out-Null

pwsh -NoProfile -ExecutionPolicy Bypass -File `
  integrations/openclaw/formation-loop/scripts/install.ps1 `
  -OpenClaw $OpenClaw `
  -Profile "active-memory" `
  -StatementWorkspace $StatementWorkspace `
  -MemoryWorkspace $MemoryWorkspace `
  -CaptureScope $CaptureScope
```

诊断：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File `
  integrations/openclaw/formation-loop/scripts/diagnose.ps1 `
  -OpenClaw $OpenClaw |
  Tee-Object `
    (Join-Path $ArtifactRoot "v313r1-baseline-diagnose.json")
```

## 7.5 自然聊天 Smoke

不得在聊天文本中要求调用工具、选择 candidate 或输出 JSON。

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File `
  integrations/openclaw/formation-loop/scripts/run-natural-chat-smoke.ps1 `
  -OpenClaw $OpenClaw `
  -SessionKey "agent:main:v313r1-baseline-write" `
  -Message "请记住：项目例会固定在每周三下午三点。"
```

查询样本：

```powershell
& $OpenClaw agent `
  --session-key "agent:main:v313r1-baseline-query" `
  --message "项目例会安排在什么时候？" `
  --json `
  --timeout 300
```

完整 baseline 数量：

```text
query relevant >= 10
NONE >= 5
write new/reuse/revision >= 12
mixed >= 8
restart >= 2
concurrency >= 2
```

脚本和样本应写入外部 `$ArtifactRoot`，不提交大 JSONL。

## 7.6 Baseline 证据

记录：

```text
Provider/model
Host sessions
hidden children
tool turns
full traversals
prompt bytes
query→visible
Capture→commit
Raw loss
duplicate/orphan
```

无真实 Provider 时，本 Gate 标记 `ENVIRONMENT_BLOCKED`，不得伪造对照数据。

---

# 8. Gate 3：应用阶段代码

## 8.1 优先方式：从任务包 Bundle 获取提交

```powershell
git fetch `
  "$TaskPackRoot\nollm_v313r1_direct_activation_stage_20260804.bundle" `
  "refs/heads/codex/aold-v313r1-direct-activation:refs/remotes/taskpack/v313r1"

git show --stat taskpack/v313r1
git cherry-pick 8182f98ffa13ddbc6bdaa788f97648c30666f236
```

如果该提交已经是 HEAD 祖先：

```powershell
git merge-base --is-ancestor `
  8182f98ffa13ddbc6bdaa788f97648c30666f236 `
  HEAD

if ($LASTEXITCODE -eq 0) {
  Write-Host "Stage commit already present; skip cherry-pick."
}
```

## 8.2 备用方式：应用 patch

仅在 Bundle fetch 不可用时：

```powershell
git apply --check `
  "$TaskPackRoot\0001-feat-openclaw-render-direct-field-encounter-activation.patch"

git am `
  "$TaskPackRoot\0001-feat-openclaw-render-direct-field-encounter-activation.patch"
```

发生冲突：

```powershell
git am --abort
```

然后逐文件理解后人工迁移，不得直接 `-X theirs`。

## 8.3 阶段代码范围

阶段提交预计修改：

```text
formation-loop Python bridge；
field_encounter；
memory_loop；
TypeScript plugin wiring；
Python tests；
Node tests。
```

必须确认没有新增：

```text
MODEL_ADAPTER
MemoryActivationPacket
activation_epoch
ModelIdentity
PrefixKV production
persistent activation cache
额外 Provider call
```

## 8.4 Checkpoint push

```powershell
git status -sb
git log --oneline -5
git push -u origin $Branch
```

### Gate 3 PASS

```text
阶段提交已进入当前分支；
基于最新 main；
无冲突未处理；
GitHub 已收到代码 checkpoint。
```

---

# 9. Gate 4：Direct Activation 离线验证

## 9.1 Targeted Python

```powershell
$env:PYTHONPATH = @(
  "$RepoRoot\packages\nollm-core\src",
  "$RepoRoot\packages\nollm-snapshot\src",
  "$RepoRoot\packages\nollm-trace\src",
  "$RepoRoot\packages\nollm-access\src",
  "$RepoRoot\integrations\openclaw\formation-loop\python",
  "$RepoRoot\reference\python"
) -join ";"

python -m pytest -q `
  integrations/openclaw/formation-loop/tests/test_openclaw_field_encounter.py `
  integrations/openclaw/formation-loop/tests/test_memory_loop.py
```

阶段包生成时已验证：

```text
25 passed
```

执行时必须重新跑，不得直接引用该数字。

## 9.2 OpenClaw Python 全量

```powershell
python -m pytest -q `
  integrations/openclaw/formation-loop/tests
```

## 9.3 Node

```powershell
Push-Location integrations/openclaw/formation-loop
try {
  npm ci
  npm test
  npm run plugin:check
} finally {
  Pop-Location
}
```

## 9.4 禁止抽象静态扫描

```powershell
$ProductionRoots = @(
  "packages",
  "integrations/openclaw"
)

$Forbidden = @(
  "MemoryActivationPacket",
  "nollm-model-adapter",
  "activation_epoch",
  "ModelIdentity",
  "PrefixKVActivation"
)

foreach ($term in $Forbidden) {
  $matches = Get-ChildItem $ProductionRoots -Recurse -File |
    Select-String -SimpleMatch $term
  if ($matches) {
    $matches | Format-Table Path, LineNumber, Line
    throw "Forbidden production abstraction found: $term"
  }
}
```

研究文档命中不属于生产违规。

## 9.5 行为矩阵

必须覆盖：

```text
相同输入确定输出；
current Statement；
失效 ID 跳过；
全部失效 → NONE；
Unicode；
预算边界；
顺序；
无 query 排序；
无持久文件；
renderer 异常失败开放；
run 结束无 activation state。
```

## 9.6 Checkpoint commit + push

若在应用阶段代码后修复了问题：

```powershell
git add integrations/openclaw/formation-loop
git diff --cached --check
git commit -m "test(aold): close direct encounter activation offline gates"
git push origin $Branch
```

无新增变更则只确认远端：

```powershell
git push origin $Branch
```

---

# 10. Gate 5：真实 Direct Activation Live

重复 Gate 2 的同一批样本，不能换题规避对照。

硬条件：

```text
query: hidden Reader child = 0
write: Cartographer child = 0
mixed: full traversal = 1
single-entry = 100%
NONE 不注入
query 不 mutation
Raw Capture loss = 0
duplicate/orphan = 0
Provider 失败开放
```

## 10.1 插件重新安装/刷新

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File `
  integrations/openclaw/formation-loop/scripts/install.ps1 `
  -OpenClaw $OpenClaw `
  -Profile "active-memory" `
  -StatementWorkspace $StatementWorkspace `
  -MemoryWorkspace $MemoryWorkspace `
  -CaptureScope $CaptureScope
```

## 10.2 重启

使用当前 OpenClaw 官方/本机 Gateway 管理命令。先记录：

```powershell
Get-ScheduledTask -ErrorAction SilentlyContinue |
  Where-Object TaskName -eq "OpenClaw Gateway"
```

若实际环境通过其他方式运行 Gateway，记录准确命令，不猜测。

## 10.3 并发样本

PowerShell 示例：

```powershell
$jobs = @()
$jobs += Start-Job -ScriptBlock {
  param($OpenClaw)
  & $OpenClaw agent `
    --session-key "agent:main:v313r1-concurrent-a" `
    --message "项目例会是什么时间？" `
    --json --timeout 300
} -ArgumentList $OpenClaw

$jobs += Start-Job -ScriptBlock {
  param($OpenClaw)
  & $OpenClaw agent `
    --session-key "agent:main:v313r1-concurrent-b" `
    --message "我们下次例会安排在哪天几点？" `
    --json --timeout 300
} -ArgumentList $OpenClaw

$jobs | Wait-Job | Receive-Job
$jobs | Remove-Job
```

## 10.4 前后对照

输出至少：

```text
样本数
success / NONE / failure
Host session count
Provider calls
tool turns
prompt bytes
local render ms
query→visible p50/p95/max
Capture→commit p50/p95/max
Provider wall-time ratio
duplicate/orphan
Raw loss
```

不得只报告优化后。

---

# 11. Gate 6：有限旧路径退出

先生成：

```text
docs/architecture/module-ownership/DIRECT_ACTIVATION_PATH_MAP.md
```

每项记录：

```text
caller
consumer
Provider call count
semantic behavior
persistence
tests
status:
  KEEP_ACTIVE
  ADAPT_TO_SHARED_RENDERER
  MIGRATION_ONLY
  REMOVABLE_AFTER_LIVE
```

只有同时满足：

```text
真实 Live 覆盖；
activity imports = 0；
迁移能力有替代；
测试完整；
lifecycle = REMOVABLE；
```

才允许：

```powershell
git rm -- <explicit-path>
```

禁止：

```powershell
git rm -r integrations/openclaw
git rm -r reference
git clean -xfd
```

删除后：

```powershell
python tools/generate_module_ownership_manifest.py --write
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/MODULE_BOUNDARY_REPORT.json
python tools/check_active_tree_assets.py
```

Checkpoint：

```powershell
git add -A
git diff --cached --check
git commit -m "chore(openclaw): retire live-verified duplicate activation paths"
git push origin $Branch
```

若无路径达到 REMOVABLE，明确报告“本 Gate 零删除”，不要为了清理而删除。

---

# 12. Gate 7：完整回归

## 12.1 Core

```powershell
$env:PYTHONPATH = "$RepoRoot\packages\nollm-core\src"
python -m pytest -q packages/nollm-core/tests
```

## 12.2 Snapshot

```powershell
$env:PYTHONPATH = @(
  "$RepoRoot\packages\nollm-core\src",
  "$RepoRoot\packages\nollm-snapshot\src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests
```

## 12.3 Trace

```powershell
$env:PYTHONPATH = @(
  "$RepoRoot\packages\nollm-core\src",
  "$RepoRoot\packages\nollm-trace\src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests
```

## 12.4 Access

```powershell
$env:PYTHONPATH = @(
  "$RepoRoot\packages\nollm-core\src",
  "$RepoRoot\packages\nollm-snapshot\src",
  "$RepoRoot\packages\nollm-access\src"
) -join ";"
python -m pytest -q packages/nollm-access/tests
```

## 12.5 OpenClaw Python

```powershell
$env:PYTHONPATH = @(
  "$RepoRoot\packages\nollm-core\src",
  "$RepoRoot\packages\nollm-snapshot\src",
  "$RepoRoot\packages\nollm-trace\src",
  "$RepoRoot\packages\nollm-access\src",
  "$RepoRoot\integrations\openclaw\formation-loop\python",
  "$RepoRoot\reference\python"
) -join ";"

python -m pytest -q integrations/openclaw/formation-loop/tests
```

## 12.6 M0 / Architecture / Hygiene

```powershell
python -m pytest -q reference/python/tests/m0

python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py
```

## 12.7 GRF

```powershell
python -m pytest -q reference/python/tests/grf
```

若仅有已知 `zstandard` 缺失：

```text
精确列出失败测试；
记录 pip/registry 安装尝试；
不得把其他失败并入该豁免。
```

## 12.8 Node

```powershell
Push-Location integrations/openclaw/formation-loop
try {
  npm ci
  npm test
  npm run plugin:check
} finally {
  Pop-Location
}
```

## 12.9 Governance

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py

python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/MODULE_BOUNDARY_REPORT.json

python tools/check_active_tree_assets.py
```

## 12.10 Compile / Git

```powershell
python -m compileall -q `
  packages `
  integrations `
  reference/python

git diff --check
git status -sb
git fsck --full
```

### Gate 7 PASS

```text
production violations = 0
cycles = []
unclassified = 0
AGENTS = 0 bytes
无功能回归
环境限制精确记录
```

---

# 13. Gate 8：状态、报告与下一任务书

生成：

```text
docs/project/V3_13_REV1_DIRECT_ACTIVATION_REPORT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

报告必须区分：

```text
已验证事实
合理判断
环境依赖
未验证事项
known limitations
```

必须记录：

```text
旧/新调用拓扑
真实读取耗时
真实写入耗时
Provider 占比
本地占比
query/write/mixed
restart/concurrency
删除和保留 Legacy
预计/实际向量
全部模块实际完成度
```

## 13.1 新任务书的 GitHub 要求

若 Provider Live 未闭合，下一任务书必须继续要求：

```text
每个大 Gate commit；
每个 checkpoint push；
分支与 main 保持可比较；
环境阻断不阻止提交真实进展；
最终 Bundle；
不得长期只保存在本地。
```

Checkpoint：

```powershell
git add docs
git diff --cached --check
git commit -m "docs(aold): record V3.13 Rev1 capability and limitations"
git push origin $Branch
```

---

# 14. Gate 9：GitHub 最终交付

## 14.1 推送当前分支

```powershell
git fetch origin --prune
git status -sb
git push -u origin $Branch
```

## 14.2 创建或更新 PR

创建 PR：

```powershell
$PrBody = Join-Path $ArtifactRoot "V3_13_REV1_PR_BODY.md"

@"
## What changed
- Direct Field Encounter activation
- no Packet/Adapter/epoch production layer
- Provider/Host validation and latency evidence
- lifecycle/boundary truth

## Validation
- list exact test commands and results
- list environment-blocked Gates

## Limitations
- Provider/Windows/Node limits, if any
"@ | Set-Content $PrBody -Encoding utf8

gh pr create `
  --draft `
  --base main `
  --head $Branch `
  --title "V3.13 Rev1 direct encounter activation" `
  --body-file $PrBody
```

若 PR 已存在：

```powershell
gh pr view $Branch --json number,url,state
```

## 14.3 进入 main

若仓库允许且所有 Final Gate 通过，优先保留线性历史：

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git merge --ff-only $Branch
git push origin main
```

若 branch protection 要求 PR：

```text
将 PR 标记 ready；
等待/运行必需检查；
使用 merge 或 rebase 策略不得 squash 本任务的有意义 checkpoint；
确认 main 包含全部提交。
```

不要 force push。

## 14.4 删除短期分支

仅在 main 已包含该分支 tip 后：

```powershell
git fetch origin
$Tip = (git rev-parse $Branch).Trim()
git merge-base --is-ancestor $Tip origin/main
if ($LASTEXITCODE -ne 0) {
  throw "Branch is not contained in origin/main."
}

git push origin --delete $Branch
git branch -d $Branch
git remote prune origin
```

如任务包创建的占位分支：

```text
codex/aold-v313r1-direct-activation-8182f98
```

仍存在且没有独有提交，也按同一安全条件删除。

---

# 15. Gate 10：完整历史 Bundle

```powershell
$FinalHead = (git rev-parse HEAD).Trim()
$ShortHead = (git rev-parse --short=8 HEAD).Trim()

$BundlePath = Join-Path $BundleRoot `
  "nollm_aold_v313r1_direct_activation_provider_live_20260804_$ShortHead.bundle"

git bundle create $BundlePath --all
git bundle verify $BundlePath

$BundleSha = (Get-FileHash $BundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
$BundleBytes = (Get-Item $BundlePath).Length

[pscustomobject]@{
  path = $BundlePath
  bytes = $BundleBytes
  sha256 = $BundleSha
  head = $FinalHead
} | ConvertTo-Json |
  Set-Content `
    (Join-Path $ArtifactRoot "V3_13_REV1_BUNDLE_RECEIPT.json") `
    -Encoding utf8
```

最终：

```powershell
git diff --check
git status --short
```

必须为空。

---

# 16. 环境受限跳过规则

## 16.1 允许跳过

仅限：

```text
真实 OpenClaw Host 不存在；
Provider 凭据不可用；
Node 24 不可安装；
npm registry 不可访问；
Windows 特有服务在非 Windows 环境；
zstandard 在当前 registry 不可获得；
GitHub 网络或认证不可用。
```

## 16.2 跳过时必须留下

```text
Gate 名称；
执行命令；
环境版本；
完整 stderr；
为什么不能修复；
对结论的影响；
在 Windows/Codex 中的恢复命令；
状态 = ENVIRONMENT_BLOCKED。
```

## 16.3 不允许跳过

```text
Python targeted tests；
Manifest；
Boundary；
Active tree；
AGENTS；
Git diff/status；
本地 commit；
Bundle；
代码静态禁止项。
```

GitHub push 虽可因环境被阻断，但任务不得声明最终完成。

---

# 17. Final Gate

```text
活动权威唯一；
V3.13 Rev1 为活动架构；
无正式 MODEL_ADAPTER；
无 Packet/epoch/cache；
一个活动 renderer；
修改前 baseline 和修改后对照真实或明确受阻；
single-entry；
one Writer session；
mixed one traversal；
Raw loss=0；
duplicate/orphan=0；
Manifest/Boundary/tests；
AGENTS=0；
每个大 Gate 已 commit；
每个可执行 checkpoint 已 push；
main/PR状态清楚；
工作树clean；
完整历史Bundle verify。
```

---

# 18. 非目标

```text
Soft Prefix
KV
Attention Bias
Memory Encoder
完整撤销状态机
大规模 Legacy 清理
Core 变化
multi-entry
multi-cell
多物理层 Placement
Stitch
PB 规模
History/Audit 产品
Git 历史重写
```

---

# 19. 建议提交序列

```text
docs(project): activate V3.13 Rev1 direct activation
fix(distributions): restore current authority and boundary truth
validation(aold): record current provider baseline
feat(openclaw): render direct Field Encounter activation
test(aold): close direct activation offline gates
validation(aold): compare direct activation provider latency
chore(openclaw): retire live-verified duplicate activation paths
docs(aold): record direct activation capability and limits
```

每个有真实变化的提交后执行：

```powershell
git push origin $Branch
```

---

# 20. 最终回复要求

只报告：

```text
branch / HEAD / commits；
GitHub branch / PR / main；
authority 和 HEAD 层次；
baseline Provider 结果；
renderer 收敛；
query/write/mixed；
calls/sessions/tools；
read/write p50/p95/max；
Raw loss/duplicate/orphan；
removed/retained Legacy；
tests/Manifest/boundary；
AGENTS；
实际向量和完成度；
ENVIRONMENT_BLOCKED；
Bundle filename/bytes/SHA。
```
