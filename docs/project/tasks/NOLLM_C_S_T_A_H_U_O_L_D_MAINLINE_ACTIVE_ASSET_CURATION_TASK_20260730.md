# Nollm 全模块：Main 主线整合与活动资产整理任务书

**任务文件名**：`NOLLM_C_S_T_A_H_U_O_L_D_MAINLINE_ACTIVE_ASSET_CURATION_TASK_20260730.md`  
**日期**：2026-07-30  
**影响模块**：`C=CORE | S=SNAPSHOT | T=TRACE | A=ACCESS | H=HISTORY | U=AUDIT | O=OPENCLAW | L=LAB | D=DISTRIBUTIONS`  
**直接修改重点**：`L + D + repository governance`  
**可验证结果**：完整 V3.12 线性历史进入 GitHub `main`；历史和生成资产移出活动工作树及 GitHub 当前树；已被 `main` 覆盖的本地、远端分支和多余 worktree 被安全删除；活动代码、迁移资产、Git 历史和 tags 完整保留  
**输入 Bundle**：`nollm_aold_unified_field_encounter_20260728_7e60875(1).bundle`  
**输入 Bundle SHA-256**：`1b0c6b4d95256ae0d8c4aececd7489bad8424c7bd61a2b02c46bea2bec888269`  
**输入 HEAD**：`7e608754b939d564f1387650f25424f2cd943f33`  
**GitHub 仓库**：`awdawmip/Nollm`  
**审核时 GitHub main**：`3b9ebc3492fb0fb1877b1e3cadeb20212a55911d`  
**主环境**：Windows 10/11、PowerShell、Git、GitHub CLI  
**交付**：所有真实进展 commit；最终工作树 clean；仓库外历史资产归档；仓库外单一完整历史 Git Bundle  
**重要边界**：本任务删除的是 GitHub 当前树和分支引用，不使用 `filter-repo` 重写历史；历史文件仍可从旧 commit 和归档中恢复  
**AGENTS**：根目录 `AGENTS.md` 必须继续保持严格 0 bytes

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% |
LAB +5% | DISTRIBUTIONS +10%

主方向：
不扩展功能。
先修复资产真值，再将已验证历史资产迁到仓库外单一归档；
将完整线性能力历史 fast-forward 进入 main；
删除被 main 完整覆盖的本地/远端功能分支和多余 worktree；
建立生成资产不再回流 GitHub 当前树的 Gate。

范围变化：
新增 repository governance / active asset lifecycle。
不修改 V3.12 Field Encounter 公共合同；
不改变 Core 物理几何；
不重写 Git 历史；
不删除未达到 REMOVABLE 的迁移代码和兼容回归。
```

## 0.1 Gate 向量复述

每个 Gate 开始与结束记录：

```text
C0 | S0 | T0 | A0 | H0 | U0 | O0 | L+5 | D+10
```

并回答：

```text
是否修改生产代码；
是否删除迁移代码；
是否删除未合并分支；
是否重写历史；
是否保留 tags；
AGENTS.md 是否仍为 0 bytes；
归档是否可复算；
GitHub main 是否 fast-forward；
Manifest 是否与 tracked tree 一致。
```

如任何模块生产代码发生能力变化，或实际偏差超过 5%，必须更新任务名称、范围、向量和完成度矩阵，不得静默扩大。

---

# 1. 已验证基线

## 1.1 Bundle

```text
完整历史：通过；
HEAD：7e60875；
working tree：clean；
Bundle SHA-256：1b0c6b4...88269。
```

## 1.2 Git 祖先关系

```text
GitHub main 3b9ebc
  ↓ 308 commits
a6551fe
  ↓ 8 commits
42eed8e
  ↓ 8 commits
7e60875
```

精确事实：

```text
3b9ebc 是 7e60875 的祖先；
main 独有 commits：0；
7e60875 相对 main：ahead 324；
a6551fe 是 42eed8e 祖先；
42eed8e 是 7e60875 祖先；
三条功能分支无分叉。
```

## 1.3 当前测试事实

新克隆复测：

```text
Core 88 passed；
Snapshot 7 passed；
Trace 3 passed；
Access 前半组 69 passed；
多个 Access 后半文件逐项通过；
Provider/Host Live 未运行。
```

## 1.4 当前资产事实

```text
tracked files：2104；
tracked bytes：约25.3 MB；
旧 Manifest entries：2093；
旧 Manifest：
  HISTORICAL 1252；
  MIGRATION_ASSET 544；
  ACTIVE 267；
  GENERATED 30。
```

## 1.5 当前阻断

```text
python tools/generate_module_ownership_manifest.py --check
```

在输入 HEAD 失败。重新生成会新增 11 个 V3.12 文件并调整 5 个旧资产状态。

---

# 2. 全部模块任务前完成度

| 模块 | 生命周期 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 93% | 高 | 物理几何、Surface、Locality、Junction、原子状态 | 本任务仅回归 | 高风险回归，0% |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | canonical state bytes | 增量与版本迁移 | 回归，0% |
| TRACE | `IMPLEMENTED` | 40% | 中 | sink 隔离 | metrics | 回归，0% |
| ACCESS | `CAPABILITY_VALIDATED` | 98% | 高 | Unified Encounter、conditional commit | Provider scale | 回归，0% |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 0% |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 0% |
| OPENCLAW | `IMPLEMENTED` | 98% | 高 | 一套 Encounter Wire、单 Writer session | Provider/Host Live | 回归，0% |
| LAB | `CAPABILITY_VALIDATED` | 97% | 中高 | 离线矩阵和历史 Evidence | 资产混放、输出回流 | 是，+5% |
| DISTRIBUTIONS | `IMPLEMENTED` | 97% | 中 | V3.12 Wire/Profile | Manifest 失真、main 远端落后 | 是，+10% |

---

# 3. 全部模块任务后目标完成度

| 模块 | 任务前 | 目标 | 预计变化 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 93% | 93% | 0 | 无代码变化 | 88+ tests、diff | 多层/Stitch |
| SNAPSHOT | 50% | 50% | 0 | 无代码变化 | package tests | 增量/version |
| TRACE | 40% | 40% | 0 | 无代码变化 | package tests | metrics |
| ACCESS | 98% | 98% | 0 | 无代码变化 | 150 tests或精确环境说明 | Provider scale |
| HISTORY | 10% | 10% | 0 | 无 | boundary | 暂停 |
| AUDIT | 10% | 10% | 0 | 无 | boundary | 暂停 |
| OPENCLAW | 98% | 98% | 0 | 无功能变化 | Python/Node回归 | Provider Live |
| LAB | 97% | 99% | 治理提升 | 外置 Evidence、可复算归档、输出根目录 | archive verify | 长期实验 |
| DISTRIBUTIONS | 97% | 99% | 治理提升 | main、Manifest、branch/tree真值 | GitHub/API/Git证据 | 正式发布 |

目标不是永久完成度。

---

# 4. 明确非目标

不得启动：

```text
新的 Nollm 功能；
Provider/Host Live；
Core API 变化；
Field Encounter 语义变化；
多物理层 Placement；
Stitch；
History/Audit 产品；
PB 压测；
Provider 更换；
模型训练；
Git 历史过滤；
tag 清理；
安全和权限系统。
```

---

# 5. Gate 0：保全现场与远端真值

## 5.1 从 Bundle 新克隆

```powershell
git clone `
  "<NOLLM_ROOT>\bundles\nollm_aold_unified_field_encounter_20260728_7e60875.bundle" `
  "<NOLLM_ROOT>\worktrees\nollm-mainline-curation"
```

不得 reset、clean 或覆盖已有工作区。

## 5.2 验证

记录：

```text
Bundle filename/SHA；
bundle verify；
HEAD；
branch；
status；
recent graph；
git fsck；
git worktree list --porcelain；
git show-ref；
git remote -v。
```

## 5.3 连接真实 GitHub

```powershell
git remote set-url origin https://github.com/awdawmip/Nollm.git
gh --version
gh auth status
git fetch origin --prune --tags
```

必须重新读取：

```text
origin/main；
default branch；
远端全部 heads；
开放 PR；
branch protection；
当前 main 的 AGENTS.md；
远端 tags。
```

审核时 main 为 `3b9ebc`，但执行时不能盲信。若已变化，按实时状态重新计算。

## 5.4 根目录 AGENTS

```text
exists；
bytes=0；
SHA-256=e3b0c442...b855；
Git blob=e69de29b...5391。
```

不得回写内容。

### Gate 0 PASS

```text
现场完整；
远端可访问；
main 真值已记录；
所有 worktree/branch/ref 已盘点；
dirty worktree 未被删除。
```

---

# 6. Gate A：修复 Ownership Manifest

这是任何批量资产移动前的硬前置。

## 6.1 重新生成

```powershell
python tools/generate_module_ownership_manifest.py --write
python tools/validate_module_ownership_manifest.py
python tools/generate_module_ownership_manifest.py --check
```

预期至少：

```text
tracked files=2104；
新增11个V3.12路径；
旧V3.11活动材料降为历史；
unclassified=0。
```

实际数量以当前远端合并后的工作树为准。

## 6.2 人工复核 V3.12

至少复核：

```text
V3.12架构；
V3.12任务书；
V3.12当前状态；
V3.12 Ledger；
FieldEncounter source/tests；
OpenClaw FieldEncounter source/tests；
当前 Distribution Wire；
当前 capability report。
```

当前唯一能力报告可保留为 `ACTIVE_CAPABILITY_RECORD`，不得因生成器默认规则误归为可立即删除历史。

## 6.3 新分类文件

生成：

```text
docs/architecture/module-ownership/ACTIVE_ASSET_CURATION_PLAN.json
docs/architecture/module-ownership/ACTIVE_ASSET_CURATION_PLAN.csv
```

分类：

```text
KEEP_ACTIVE
KEEP_ACTIVE_FIXTURE
KEEP_MIGRATION
KEEP_LEGACY_REGRESSION
ARCHIVE_HISTORICAL
ARCHIVE_GENERATED
BLOCKED_ACTIVE_DEPENDENCY
REMOVE_BRANCH_AFTER_MAIN
REMOVE_WORKTREE_AFTER_MAIN
```

每个移出文件记录：

```text
path；
owner；
old lifecycle；
reason；
imported_by；
archive destination；
Git blob；
bytes；
SHA-256；
replacement；
removal safety。
```

### Gate A PASS

```text
Manifest与tracked tree一致；
0 unclassified；
所有移出候选逐文件可解释；
未根据目录名直接删除；
当前能力报告未误删。
```

建议提交：

```text
fix(distributions): restore ownership manifest truth
```

---

# 7. Gate B：建立活动仓库资产政策

生成：

```text
docs/project/NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md
```

唯一规则：

## 7.1 允许进入 GitHub 当前树

```text
活动 source；
活动 package tests；
必要 fixtures；
当前最高原则；
当前项目书/架构/路线；
ACTIVE_PROJECT；
CURRENT_STATUS；
Module Ledger；
当前任务；
当前能力记录；
模块章程；
发行组合；
可执行治理工具；
少量稳定示例。
```

## 7.2 不进入 GitHub 当前树

```text
Git Bundle；
ZIP/TAR归档；
冻结 Live JSONL；
运行日志；
Provider transcript；
delivery receipt；
旧任务书全集；
旧状态全集；
旧 starting-state 全集；
实验 results；
生成报告副本；
外部 artifact manifest；
临时 worktree；
模型 corpus 输出；
round receipts。
```

## 7.3 尚未 REMOVABLE 的资产

```text
迁移代码；
compatibility re-export；
legacy regression；
当前旧 Wire 迁移见证；
reference 中仍被活动测试引用的部分。
```

继续留在当前树，不得因“目录乱”直接删除。

### Gate B PASS

```text
政策单一；
不把任务细节复制到AGENTS；
不把历史归档放回仓库。
```

---

# 8. Gate C：仓库外历史资产归档

## 8.1 归档目录

默认：

```text
<NOLLM_ROOT>\archives\
```

归档文件：

```text
NOLLM_HISTORICAL_ASSETS_20260730_<inputhead>.zip
```

不得创建在 Git repo 内。

## 8.2 归档内容

按 Gate A 清单，优先包括：

```text
manifest=HISTORICAL；
不被活动代码或测试引用的GENERATED；
docs/delivery；
docs/validation；
docs/integration/openclaw/evidence；
旧docs/project tasks/reports/starting-state；
experiments/grf/results；
validation/live；
validation/frozen；
历史validation JSON/JSONL；
lab results/runs/runtime_truth；
历史Provider Evidence；
历史examples receipts；
根目录F0 delivery receipts；
旧V1交付草案；
旧external artifact manifests。
```

路径清单不是盲删规则，最终以逐文件分类为准。

## 8.3 归档自描述

ZIP 根目录必须含：

```text
ARCHIVE_README.md
ARCHIVE_MANIFEST.json
ARCHIVE_MANIFEST.csv
SOURCE_GIT_HEAD.txt
SOURCE_BUNDLE_SHA256.txt
```

每个文件记录：

```text
original_path；
size；
SHA-256；
Git blob SHA；
lifecycle；
owner；
reason；
archived_at；
replacement/current authority。
```

## 8.4 双重校验

归档后：

```text
ZIP可打开；
entry count与计划一致；
每个entry SHA-256一致；
总字节一致；
随机抽样；
全量脚本复算。
```

归档校验通过前不得 `git rm`。

### Gate C PASS

```text
仓库外单一归档完整；
清单可复算；
没有活动文件；
没有未保全删除。
```

---

# 9. Gate D：从活动工作树移除历史和生成资产

## 9.1 删除方式

只对已归档且 Gate A 标记为：

```text
ARCHIVE_HISTORICAL
ARCHIVE_GENERATED
```

执行显式：

```powershell
git rm -- <path-list>
```

禁止：

```powershell
git rm -r docs
git rm -r reference
git clean -xfd
```

## 9.2 活动控制文件最小集

至少保留：

```text
docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_12_...
docs/architecture/NOLLM_CONTENT_NEUTRALITY_AND_MEMORY_ELIGIBILITY_DECISION_20260723.md
docs/project/NOLLM_PROJECT_BOOK_V3_1_...
docs/project/NOLLM_PROJECT_BOOK_V3_4_...
docs/project/NOLLM_ROUTE_BOOK_V3_9_...
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
当前任务书
当前能力记录
各模块章程
```

实际活动集以 `ACTIVE_PROJECT` 和模块章程为准。

## 9.3 更新引用

修复：

```text
README；
ARCHITECTURE；
ROADMAP；
ACTIVE_PROJECT；
CURRENT_STATUS；
Ledger；
文档链接；
脚本默认输出路径；
测试fixture路径。
```

历史引用改为：

```text
Git commit/tag；
外部归档文件名和SHA；
不得引用本机绝对私有路径作为唯一来源。
```

## 9.4 预期效果

预估：

```text
tracked files：从2104降至约800～1100；
当前树体积显著下降；
实际数字以依赖审计为准，不设伪精确硬指标。
```

### Gate D PASS

```text
活动source/tests完整；
历史文件从当前树消失；
归档仍可复算；
no broken links；
AGENTS仍为空。
```

建议提交：

```text
chore(repo): move historical assets out of active tree
```

---

# 10. Gate E：防止生成资产回流

## 10.1 `.gitignore`

加入精确规则，至少阻止：

```text
*.bundle
*.zip
*.tar
*.tar.gz
*.7z
validation/live/
validation/frozen/
**/results/
**/runs/
**/runtime_truth/
**/receipts/
```

如某路径包含活动 fixture，不得使用过宽 glob；改用精确目录或 `.gitkeep`/README。

## 10.2 外部输出根

统一：

```text
NOLLM_ARTIFACT_ROOT=<NOLLM_ROOT>\artifacts
NOLLM_ARCHIVE_ROOT=<NOLLM_ROOT>\archives
NOLLM_BUNDLE_ROOT=<NOLLM_ROOT>\bundles
```

活动 Lab/validation 脚本默认输出仓库外；测试可使用临时目录。

## 10.3 Gate 工具

新增：

```text
tools/check_active_tree_assets.py
```

检查：

```text
禁止bundle/archive进入Git；
禁止冻结Evidence进入活动目录；
禁止超限生成JSONL；
禁止旧delivery receipt回流；
允许显式active fixture allowlist；
AGENTS=0 bytes。
```

### Gate E PASS

```text
新运行不会再次污染工作树；
Gate可在Windows和Linux执行；
不误伤active fixtures。
```

建议提交：

```text
build(repo): route generated evidence outside Git
```

---

# 11. Gate F：建立真实 `main`

## 11.1 不新建长期功能分支

本任务直接在本地 `main` 整合：

```powershell
git fetch origin --prune --tags
git switch -C main origin/main
git merge --ff-only 7e608754b939d564f1387650f25424f2cd943f33
```

如果资产清理提交已在原功能分支完成，则：

```powershell
git merge --ff-only <curation-head>
```

但最终 main 必须包含：

```text
3b9ebc → ... → 7e60875 → curation commits
```

不得 squash 324 commits。

## 11.2 main 变化处理

若执行时 `origin/main` 已不是 `3b9ebc`：

```text
重新fetch；
计算merge-base；
若新main仍是curation HEAD祖先：继续ff-only；
若有main独有提交：停止直接push，建立整合报告；
不得force；
不得丢弃main新提交。
```

## 11.3 非标准 ref

确认：

```text
refs/main-worktree/HEAD
```

已被 main 覆盖后：

```powershell
git update-ref -d refs/main-worktree/HEAD
```

### Gate F PASS

```text
local main存在；
main包含完整历史；
无merge commit；
无rebase；
无squash；
无force；
status clean。
```

---

# 12. Gate G：推送 GitHub main

## 12.1 推送前

```powershell
git fetch origin main
git merge-base --is-ancestor origin/main main
git log --left-right --count origin/main...main
git diff --check
git status --short
```

必须：

```text
origin/main独有=0；
local main ahead>0；
working tree clean。
```

## 12.2 推送

```powershell
git push origin main:main
```

不使用：

```text
--force
--force-with-lease
```

## 12.3 GitHub 校验

通过 GitHub API/CLI复核：

```text
default branch=main；
main HEAD=local main HEAD；
AGENTS.md=0 bytes；
活动V3.12文件存在；
历史归档文件不在当前树；
bundle/zip不在当前树；
Manifest与GitHub tree一致。
```

### Gate G PASS

```text
GitHub main fast-forward成功；
没有历史改写；
当前树与本地clean main一致。
```

---

# 13. Gate H：安全删除分支和 worktree

## 13.1 远端分支实时盘点

```powershell
git ls-remote --heads origin
gh pr list --state all --limit 200
```

每个分支必须记录：

```text
name；
tip；
是否main祖先；
ahead/behind；
是否有开放PR；
是否被worktree占用；
是否dirty；
处理决定。
```

## 13.2 可删除条件

只有同时满足：

```text
branch != main；
git merge-base --is-ancestor <branch-tip> main 成功；
无开放PR或PR已合并/关闭；
无dirty worktree；
无独有commit；
不承担release/tag身份。
```

才允许删除。

## 13.3 已知候选

如果远端实际存在，以下均应在 main 后删除：

```text
codex/aold-content-neutral-formation-recoverable-absorption-routing
codex/aold-single-content-neutral-tool-evidence-capture-continuation
codex/aold-unified-field-encounter-read-write-duality
```

因为审核时三者均为 main 新 HEAD 的祖先。

## 13.4 远端删除

```powershell
git push origin --delete <branch>
```

## 13.5 本地删除

```powershell
git branch -d <branch>
git remote prune origin
```

## 13.6 Worktree

```powershell
git worktree list --porcelain
```

仅移除：

```text
clean；
branch已进入main；
无未跟踪用户数据；
无锁定进程；
已生成worktree inventory。
```

使用：

```powershell
git worktree remove <path>
git worktree prune
```

dirty、locked、未知 worktree：

```text
保留；
记录；
不得强删。
```

## 13.7 Tags

全部保留。不得因 tag 多而删除。

### Gate H PASS

```text
本地长期分支只剩main；
远端已合并功能分支删除；
未合并分支完整保留；
worktree清楚；
remote refs已prune。
```

建议提交不需要包含 branch 删除；分支拓扑作为状态证据记录。

---

# 14. Gate I：全量回归

## 14.1 Manifest / Boundary

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/MAINLINE_ASSET_CURATION_BOUNDARY_REPORT.json
python tools/check_active_tree_assets.py
```

要求：

```text
tracked count一致；
unclassified=0；
production violations=0；
production cycles=[]。
```

## 14.2 Package

```text
Core；
Snapshot；
Trace；
Access；
OpenClaw Python；
OpenClaw Node/build；
Distribution；
M0/architecture/hygiene；
compileall。
```

Access 必须在实际 Windows 主环境完整跑完。若单进程受环境影响，允许按测试文件分组，但必须：

```text
全部150项均被执行；
无重复遗漏；
汇总脚本可复算；
不能只报告部分。
```

## 14.3 归档

```text
archive entry count；
archive bytes；
archive SHA；
全量文件SHA；
随机恢复；
Git old commit恢复对照。
```

## 14.4 Git

```powershell
git fsck --full
git diff --check
git status --short
git branch -a -vv
git worktree list
git log --graph --decorate --oneline -n 80
```

### Gate I PASS

```text
代码能力无回归；
历史资产完整可取；
main唯一主线；
GitHub当前树干净；
Manifest真实；
AGENTS空；
工作树clean。
```

---

# 15. Gate J：状态和进度账

更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/NOLLM_MAINLINE_ACTIVE_ASSET_CURATION_REPORT.md
```

报告必须记录：

```text
旧main/newmain；
保留完整commit数；
归档文件名/SHA；
移出文件数/字节；
保留active/migration数；
删除本地分支；
删除远端分支；
保留分支及原因；
移除worktree；
保留dirty worktree；
Manifest；
tests；
GitHub default/head；
实际推进向量；
实际完成度；
Provider Live仍未验证。
```

建议能力状态：

```text
MAINLINE_ACTIVE_ASSET_CURATED_AT_<HEAD>
```

V3.12 状态仍保持：

```text
AOLD_UNIFIED_FIELD_ENCOUNTER_IN_PROGRESS
PROVIDER_LIVE_PENDING
```

不得因仓库清理宣称功能完成。

---

# 16. Final Gate

必须满足：

```text
main包含完整7e60875历史和清理提交；
GitHub default main=head一致；
无force/rebase/squash；
当前树无历史Evidence堆积；
外部单一归档验证通过；
Manifest check通过；
0 unclassified；
boundary=0；
cycles=[]；
所有package回归；
AGENTS=0 bytes；
所有已删分支均为main祖先；
未合并分支未删除；
tags完整；
工作树clean。
```

---

# 17. 停止条件

仅在以下情况停止：

```text
origin/main出现独有提交；
远端main不能fast-forward；
历史候选被活动source/test导入；
归档hash不一致；
候选分支含main未拥有commit；
dirty/locked worktree无法安全保全；
branch protection阻止正常fast-forward；
GitHub认证不可用；
删除资产导致真实功能回归。
```

即使停止也必须：

```text
提交已完成的安全进展；
不删除未保全文件；
工作树clean；
生成IN_PROGRESS Bundle；
如实报告阻断。
```

普通链接、Manifest分类、测试路径和文档问题应直接修复继续。

---

# 18. 建议提交序列

```text
fix(distributions): restore ownership manifest truth
docs(repo): define active repository asset policy
chore(repo): move historical assets out of active tree
build(repo): route generated evidence outside Git
test(repo): validate curated active tree
docs(repo): record mainline and asset curation
```

不得为了“提交整齐”重写已有 324 commits。

---

# 19. 单一 Bundle

最终文件：

```text
nollm_mainline_active_asset_curation_20260730_<shorthead>.bundle
```

仓库外：

```powershell
git bundle create `
  "<NOLLM_ROOT>\bundles\nollm_mainline_active_asset_curation_20260730_<shorthead>.bundle" `
  --all

git bundle verify `
  "<NOLLM_ROOT>\bundles\nollm_mainline_active_asset_curation_20260730_<shorthead>.bundle"

Get-FileHash `
  "<NOLLM_ROOT>\bundles\nollm_mainline_active_asset_curation_20260730_<shorthead>.bundle" `
  -Algorithm SHA256
```

交付：

```text
一个Git Bundle；
一个仓库外历史资产ZIP；
二者均给SHA-256；
不把二者放回GitHub。
```

---

# 20. 最终回复要求

最终只报告：

```text
main：
  old/new HEAD；
  fast-forward commits；
  force/rebase/squash=0；

assets：
  before/after files；
  archived files/bytes；
  archive filename/SHA；
  active/migration retained；
  removed top paths；

branches：
  local deleted；
  remote deleted；
  retained及原因；
  worktree removed/retained；

GitHub：
  default branch；
  main HEAD；
  current tree verification；

engineering：
  tests；
  Manifest；
  boundary/cycles；
  AGENTS；
  actual vector/completion；
  Provider Live limitation；

Bundle filename/SHA。
```
