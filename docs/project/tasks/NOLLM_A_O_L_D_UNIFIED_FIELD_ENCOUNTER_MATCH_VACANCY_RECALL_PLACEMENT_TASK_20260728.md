# Nollm AOLD：统一 Field Encounter、事实／空位终态与读写对偶闭环任务书

**任务文件名**：`NOLLM_A_O_L_D_UNIFIED_FIELD_ENCOUNTER_MATCH_VACANCY_RECALL_PLACEMENT_TASK_20260728.md`
**日期**：2026-07-28
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**可验证结果**：问题、待吸收命题和混合刺激使用同一个 Field Encounter 状态机；遇到事实后 Recall/Reuse/Revision，遇到合法空位后 Placement/NONE；普通吸收不再创建独立 Cartographer 语义 session
**任务性质**：V3.12 操作模型重构；保留 Core 物理几何、Raw Capture、内容中立、Prompt-bounded Atlas、realized Junction、single-entry 和 one Statement/Atom/Handle/Cell
**最近可核验输入 Bundle**：`nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_8f19a9b.bundle`
**输入 Bundle SHA-256**：`1b573f62d2245ab65c1a52d437ca1e7d86b1bf59cc2a1e1420a2f7e41463f8a8`
**最近可核验输入 HEAD**：`8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea`
**动态输入规则**：开工时必须读取仓库 `ACTIVE_PROJECT`、`CURRENT_STATUS`、模块进度账和当前 clean HEAD；若已领先 `8f19a9b`，以最新活动 HEAD 为真实输入，不得 reset；记录代码差异、已完成能力和任务范围偏差
**建议工作分支**：`codex/aold-unified-field-encounter-read-write-duality`
**主环境**：Windows 10/11、PowerShell、Node、真实 OpenClaw、当前 Host Provider
**交付**：大跨度单任务；内部 Gate；普通问题直接修复；所有真实进展 commit；工作树 clean；仓库外生成并验证一个完整历史 Git Bundle
**插件状态**：保持安装；正式 Provider Live 仅在离线合同、数据安全和回归 Gate 通过后执行
**数据状态**：全部旧 Raw Capture、Statement、Handle、Core state、工作区和冻结 Evidence 保留；新建独立 V3.12 Live workspace
**核心范围**：首版不修改 Core 公共合同；如实际必须修改 Core，应立即更新任务名、向量、完成度矩阵和状态记录，不得静默扩张

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
把独立 Recall 路由与独立 Placement/Cartography 路由收敛为同一
Field Encounter 状态机；
在同一渐进几何路径和同一 Locality 中同时展示已有事实和合法空位；
由事实/空位终态决定 Recall、Reuse、Revision、Placement、NONE 或 Defer；
普通后台吸收用一个隐藏 Host session 完成命题形成和场相遇，
不再另起 Cartographer 语义 session。

范围变化：
Access 新增统一 Field Encounter 公共合同和 effect resolver；
OpenClaw 主代理与后台 Writer 共享同一工具 Wire；
原始 Capture、内容中立、single-entry、Core 物理几何不变。
```

## 0.1 Gate 向量复述

每个 Gate 开始复述：

```text
C0 | S0 | T0 | A+15 | H0 | U0 | O+15 | L+15 | D+5
```

每个 Gate 结束记录：

```text
实际受影响模块；
预计/实际向量；
是否修改Core；
是否新增read/write mode；
是否存在第二套Surface导航；
是否创建独立Cartographer session；
是否新增query/fact索引；
single-entry；
stale零写；
AGENTS.md是否仍为零字节；
是否需要更新范围。
```

任一模块实际偏差超过 5%，或出现 Core 生产代码变化，必须更新：

```text
任务文件名；
受影响模块；
推进向量；
任务前/后完成度；
CURRENT_STATUS；
Module Ledger。
```

---

# 1. 开工依据与动态现场

开工时按角色读取：

```text
1. 最高原则；
2. 当前活动项目书；
3. V3.7物理场、V3.9 Coverage、V3.10 Capture、
   当前V3.11修订和V3.12统一Field Encounter；
4. CURRENT_STATUS；
5. MODULE_PROGRESS_LEDGER；
6. 当前任务书；
7. A/O/L/D模块章程和公共合同；
8. 根目录AGENTS.md；
9. 实际代码、测试和Manifest。
```

不得仅因文件日期新就认为其活动有效；以 `ACTIVE_PROJECT`、文档正文状态、代码和进度账交叉确认。

开工记录：

```text
docs/project/V3_12_UNIFIED_FIELD_ENCOUNTER_STARTING_STATE.md
```

至少记录：

```text
branch；
HEAD；
recent log；
working tree；
Bundle/SHA；
ACTIVE_PROJECT；
CURRENT_STATUS；
Ledger；
Manifest tracked/unclassified；
production violations/cycles；
各package测试；
OpenClaw Python/Node；
活动Wire；
现有Recall和Placement调用拓扑；
Provider调用数与延迟；
当前AGENTS.md字节数和SHA-256。
```

如果工作树不 clean：

```text
不得丢弃；
先识别用户修改；
提交真实进展或记录阻断；
不得reset/clean覆盖。
```

---

# 2. 全部模块任务前完成度

以最近内容中立审计重算为任务书生成基线；开工时必须按当前仓库进度账复核并回填。

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 93% | 中高 | V3.9物理几何、Surface、realized Junction、原子state | 本任务只回归 | 否 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes、restore/diff基础 | 增量/version | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | sink隔离和基础事件 | metrics/长期观察 | 否 |
| ACCESS | `IMPLEMENTED` | 86% | 中 | Statement/provenance、Atlas、Locality、Admission | 读写双状态机、内容资格/continuation漂移 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 84% | 中 | Raw Capture、worker、主代理工具基础 | Recall/Cartography分离、额外session、Live未闭合 | 是 |
| LAB | `IMPLEMENTED` | 80% | 中 | deterministic fixtures和部分Provider证据 | 缺统一操作、混合turn和调用消融 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 88% | 中 | profile/插件组合 | 活动Wire和旧路径真值 | 是 |

估值不是永久事实；若当前 HEAD 已实现后续能力，应按证据上调，不能机械复用。

---

# 3. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 93% | 93% | 0% | 无公共合同变化；全量回归 | Core/Snapshot/Trace测试、边界 | multi-cell、多层、Stitch |
| SNAPSHOT | 50% | 50% | 0% | 回归 | package tests | 增量/version |
| TRACE | 40% | 40% | 0% | 回归和Encounter事件兼容 | sink parity | metrics |
| ACCESS | 86% | 96% | +15%向量 | FieldEncounter、事实/空位卡、effect resolver、conditional commit | query/write/mixed矩阵 | 长期规模 |
| HISTORY | 10% | 10% | 0% | 无 | boundary | 暂停 |
| AUDIT | 10% | 10% | 0% | 无 | boundary | 暂停 |
| OPENCLAW | 84% | 95% | +15%向量 | 主代理与后台Writer共享Wire；一个后台语义session | 真实Host/Provider Live | 多Host/多Provider |
| LAB | 80% | 94% | +15%向量 | 读写对偶、混合turn、调用消融、延迟证据 | fixtures + live evidence | 长期统计 |
| DISTRIBUTIONS | 88% | 93% | +5% | V3.12 Wire/profile/legacy禁用 | install/diagnose/manifest | 正式发行 |

不得写永久 100%。

---

# 4. Gate 0：清空根目录 `AGENTS.md`

这是本任务第一项仓库修改，优先于架构入库、代码变更和测试。

## 4.1 要求

```text
仓库根目录AGENTS.md：
  文件必须存在；
  文件长度必须为0 bytes；
  不保留空行、BOM、空格或注释；
  不删除文件；
  不改名；
  不创建替代AGENTS文件；
  后续Gate不得重新写入任何内容。
```

本任务显式取代所有旧任务中的：

```text
更新AGENTS.md；
至少加入以下规则；
同步Authority段。
```

当前任务的架构和执行约束只保存在：

```text
活动架构书；
本任务书；
CURRENT_STATUS；
模块章程；
代码和测试。
```

## 4.2 Windows PowerShell

```powershell
$agents = Join-Path $PWD "AGENTS.md"

if (-not (Test-Path $agents)) {
    New-Item -ItemType File -Path $agents | Out-Null
}

[System.IO.File]::WriteAllBytes($agents, [byte[]]@())

$item = Get-Item $agents
if ($item.Length -ne 0) {
    throw "AGENTS.md must be exactly zero bytes."
}

$sha = (Get-FileHash $agents -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha -ne "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") {
    throw "AGENTS.md is not the canonical empty file."
}

$blob = (git hash-object AGENTS.md).Trim()
if ($blob -ne "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391") {
    throw "AGENTS.md Git blob is not empty."
}
```

## 4.3 防回写 Gate

新增只读检查脚本或现有治理 Gate：

```text
AGENTS.md exists；
size=0；
SHA-256=e3b0...b855；
Git blob=e69d...5391。
```

Final Gate 再次执行。

## 4.4 Gate 0 PASS

```text
AGENTS.md exact zero-byte；
git diff只包含预期清空；
状态记录清空原因；
后续任务权威未复制到其他Agent规则文件。
```

建议提交：

```text
chore(repo): clear root AGENTS execution overlay
```

---

# 5. Gate A：采用 V3.12 并统一活动真值

工作：

```text
加入V3.12架构书；
更新ACTIVE_PROJECT；
更新CURRENT_STATUS；
更新MODULE_PROGRESS_LEDGER；
将当前独立Recall/Placement任务重定性；
把未执行或被替换的V3.11任务标为SUPERSEDED/HISTORICAL；
保留内容中立、continuation、Raw Capture纠偏；
记录当前真实代码锚点；
保护性commit。
```

不得：

```text
删除历史任务；
伪称V3.12已实现；
把8f19a9b或更晚检查点改名成统一Field Encounter能力；
覆盖当前工作树用户数据。
```

Gate A PASS：

```text
唯一活动任务为本任务；
唯一活动操作模型为Field Encounter；
旧读写双流程只作迁移输入；
AGENTS.md仍为0 bytes。
```

建议提交：

```text
checkpoint(aold): adopt unified Field Encounter V3.12
```

---

# 6. Gate B：盘点并映射历史资产

逐文件盘点：

```text
packages/nollm-access/**
integrations/openclaw/formation-loop/**
lab/nollm-lab/**
distributions/**
```

生成：

```text
docs/architecture/module-ownership/V3_12_FIELD_ENCOUNTER_REALLOCATION.md
```

每项分类：

```text
REUSE_SHARED
ADAPT_RECALL
ADAPT_PLACEMENT
MOVE_TO_ENCOUNTER
LEGACY_MIGRATION
REMOVE_AFTER_REPLACEMENT
UNRELATED
```

至少盘点：

```text
Surface page/root/open_region；
run-scoped operation；
bounded Locality；
existing fact projection；
frontier/independent seed；
realized Junction；
revision provisional/confirmation；
AccessDecision；
Recall result mapping；
Writer/Cartographer session；
main-agent memory tool；
Capture/worker state；
profile/scope；
Provider Evidence；
legacy hidden Reader。
```

Gate B PASS：

```text
不新建第二套Surface或Core；
每项旧路径有迁移去向；
无未替代删除；
无读写mode改名后继续双路。
```

---

# 7. Gate C：Access `FieldEncounter` 公共合同

## 7.1 新对象

建议名称可按代码风格调整：

```text
FieldEncounterRequest
FieldEncounterOperation
FieldEncounterPage
EncounterFactCard
EncounterVacancyCard
FieldEncounterResult
EncounterEffect
EncounterCommitRequest
```

## 7.2 Request 禁止模式字段

AST/Schema测试禁止：

```text
intent: read/write；
mode: recall/placement；
operation_type: read/write。
```

允许：

```text
optional_pending_proposition。
```

## 7.3 统一动作

```text
surface
open_region
enter_locality
expand_same_entry
select_fact
select_vacancy
none
defer
cancel
```

## 7.4 Root identity

同一：

```text
state；
scope；
FieldScope；
budget；
Profile
```

对 query-only、write-only、mixed 请求生成完全相同 root page identity 和结构内容。

## 7.5 Gate C PASS

```text
一套Wire；
一套operation store；
一套page/path校验；
root结构与读写预设无关；
旧Recall/Placement adapter可映射进入统一合同。
```

建议提交：

```text
feat(access): introduce operation-neutral Field Encounter contract
```

---

# 8. Gate D：事实卡与合法空位卡

## 8.1 Existing fact cards

Locality 中投影：

```text
operation-local fact_id；
current Statement；
Handle；
几何路径；
revision eligibility；
provenance摘要；
expand状态。
```

## 8.2 Vacancy cards

复用现有几何资产生成：

```text
LOCAL_VACANCY；
BOUNDARY_VACANCY；
JUNCTION_VACANCY；
NEUTRAL_SEED_VACANCY。
```

每个卡绑定：

```text
GeometryAddress；
state identity；
capacity；
boundary；
relation groups；
free faces；
operation TTL。
```

## 8.3 禁止 first-empty

新增回归：

```text
stable-key最前空Cell不是关系最合适Cell；
结果不得机械选择最前空Cell；
插入顺序变化不得改变关系中立候选定义；
Junction必须all_groups_realized。
```

## 8.4 内容中立 preview

按统一固定预算投影现有事实：

```text
不按sensitive/secret/weather/role/tool分类；
不把query输入Python；
不改canonical Statement；
scope/workspace隔离。
```

Gate D PASS：

```text
同一Locality同时有事实卡和空位卡；
事实与空位均来自几何和current state；
无内容分类；
无query索引。
```

建议提交：

```text
feat(access): project facts and legal vacancies in one Locality
```

---

# 9. Gate E：语义终态与 effect resolver

## 9.1 活动关系

```text
same
revision
related_distinct
unrelated
uncertain
```

真实 LLM 选择；Access只机械验证。

## 9.2 Effect resolver

实现矩阵：

```text
no pending + fact        → recall
no pending + vacancy     → none
pending + same fact      → reuse
pending + revision fact  → provisional revision
pending + related vacancy→ local/junction placement
pending + unrelated      → neutral seed placement
uncertain                → continue/retryable defer
exhausted                → none或retryable exhausted
```

不得使用：

```text
关键词；
hash；
固定语义分数；
伪向量；
source role；
内容类别。
```

## 9.3 Mixed effect

允许同一 result：

```text
recalled_statement_ids 非空；
pending mutation effect 非空。
```

但 mutation 仍必须条件提交。

Gate E PASS：

```text
读写效果只由Encounter终态和pending载荷共同决定；
无预设mode分支；
same/revision/new语义由真实LLM产生。
```

建议提交：

```text
feat(access): resolve recall and placement from Encounter terminals
```

---

# 10. Gate F：Conditional Commit 与陈旧操作

## 10.1 提交前验证

```text
operation未过期；
scope/workspace一致；
Core state identity一致；
fact仍current；
vacancy仍空；
capacity仍合法；
revision provisional一致；
pending proposition identity一致。
```

## 10.2 结果类型

明确：

```text
not_committed；
committed_and_verified；
committed_readback_unknown；
stale_zero_write；
retryable_conflict。
```

不得用一个普通 exception 混淆“未提交”和“可能已提交”。

## 10.3 原子性矩阵

```text
Statement写失败；
Handle写失败；
Core写失败；
readback失败；
vacancy竞争；
stale state；
restart；
confirmed revision replay；
BaseException边界；
direct Core竞争回归。
```

保留或恢复历史被删除的重要测试场景。

Gate F PASS：

```text
stale=零写；
未确认revision=零写；
duplicate/orphan=0；
结果状态明确；
Core公共合同不变。
```

建议提交：

```text
fix(access): condition Encounter effects on current field state
```

---

# 11. Gate G：OpenClaw 主代理统一工具

## 11.1 Tool Wire

活动工具：

```text
nollm_field_encounter
```

同一工具支持：

```text
surface；
open_region；
enter_locality；
expand_same_entry；
select_fact；
select_vacancy；
none；
defer。
```

不再分别暴露：

```text
Recall-only tool；
Placement-only Cartography tool。
```

## 11.2 主代理 query-only

```text
用户问题
→ user Raw Capture
→ 主代理同run Field Encounter
→ fact→Recall
→ vacancy/exhausted→NONE
→ visible answer
→ assistant Raw Capture
```

硬Gate：

```text
hidden Reader child calls=0；
single-entry=100%；
query不传Python语义搜索；
NONE不产生write。
```

## 11.3 混合 turn

至少支持：

```text
“我下周改在周三开会。上次约的地点在哪里？”
```

同一 operation：

```text
召回旧地点；
形成新时间命题；
选择reuse/revision/vacancy；
不进行第二次完整Surface Traversal。
```

如Host生命周期要求 mutation 延后，允许在同 operation result 后由后台提交，但不得重新导航。

Gate G PASS：

```text
main-agent一套工具；
query-only和mixed真实运行；
无hidden Reader；
无独立第二次Traversal。
```

建议提交：

```text
feat(openclaw): use Field Encounter in the main agent run
```

---

# 12. Gate H：后台 Encounter Writer 单 session

## 12.1 Common path

```text
Raw Capture batch
→ one hidden Host session
→ proposition formation
→ same session calls Field Encounter
→ terminal selection
→ conditional commit
```

## 12.2 禁止

```text
Formation session结束；
再创建Cartographer session。
```

## 12.3 Continuation

必须保留：

```text
oversize Capture windows；
statement continuation；
retryable defer；
evaluation identity；
Raw coverage certificate。
```

预算不能导致内容静默跳过。

## 12.4 多命题

首版允许：

```text
一个session形成多个命题；
每个命题独立Encounter terminal；
复用同一root/page缓存；
不得共享错误fact/vacancy选择；
逐命题原子提交。
```

如实现风险过高，可以每命题独立 operation，但仍复用同一 Host session，不能创建独立Cartographer agent。

Gate H PASS：

```text
common batch hidden semantic sessions=1；
Cartographer child sessions=0；
oversize/continuation不回退；
duplicate/orphan=0。
```

建议提交：

```text
feat(openclaw): continue proposition formation into Field Encounter
```

---

# 13. Gate I：自动验证矩阵

## 13.1 Query-only

```text
exact relevant fact→Recall；
related Locality→Recall；
no corresponding fact→vacancy/NONE；
exhausted→NONE；
无mutation；
same root identity；
single-entry。
```

## 13.2 Proposition-only

```text
exact duplicate→reuse；
near duplicate由LLM决定same/revision；
revision→provisional/confirmed；
related-distinct→local vacancy；
multi-group→realized Junction vacancy；
unrelated→neutral seed；
uncertain→retryable defer。
```

## 13.3 Mixed

```text
旧事实问题+新事实；
旧事实问题+旧事实修订；
NONE问题+新独立事实；
Recall结果+assistant新推论；
同operation；
一次root traversal；
effect和answer均正确。
```

## 13.4 结构

```text
query/write/mixed root Surface相同；
128/300/1000字段Prompt有界；
page完整；
无stable-key抽样；
fact/vacancy ID operation-local；
path不持久化；
无read/write mode字段。
```

## 13.5 防漂移

静态扫描：

```text
Topic/Entity/query/fact index=0；
vector/graph/embedding=0；
Python semantic relation branch=0；
persistent Cursor/path=0；
multi-entry=0；
Core query/Statement语义=0。
```

---

# 14. Gate J：真实 Provider / Host Live

仅在 Gate 0-I 全部通过后运行。

## 14.1 新工作区

```text
nollm-aold-unified-field-encounter-v12
```

旧数据全部保留。

## 14.2 样本

至少：

```text
query-only relevant >= 10；
query-only NONE >= 5；
write-only new/reuse/revision >= 15；
mixed turns >= 10；
related vacancy >= 3；
neutral seed >= 3；
revision confirmation >= 2；
Gateway restart >= 2；
concurrent sessions >= 2。
```

普通自然聊天，不得在用户文本中指示：

```text
调用工具；
选择candidate；
写Nollm；
输出JSON；
指定地址。
```

## 14.3 可复算指标

```text
Capture publish；
Field Encounter operations；
root/page/path；
fact/vacancy cards；
semantic terminal；
effect；
Provider/model；
Host session count；
tool turns；
query→visible；
Capture→terminal；
terminal→commit；
duplicate/orphan；
single-entry；
hidden child；
restart；
NONE。
```

## 14.4 关键消融

对相同 fixture 比较：

```text
旧Formation+Cartographer双session；
新Encounter Writer单session。
```

记录：

```text
session数；
Provider wall time；
Prompt bytes；
tool turns；
最终语义结果；
写入/召回正确性。
```

不得只报告新路径，不报告旧对照。

Gate J PASS：

```text
真实read/write/mixed共享Wire；
普通吸收无独立Cartographer session；
主代理hidden Reader=0；
single-entry=100%；
Raw Capture loss=0；
duplicate/orphan=0；
至少一个真实混合turn只遍历一次；
状态诚实。
```

---

# 15. Gate K：回归、状态与发行真值

## 15.1 分组回归

Windows PowerShell，按仓库实际命令运行并记录：

```text
Core；
Snapshot；
Trace；
Access；
OpenClaw Python；
OpenClaw Node/build；
Lab；
M0；
Manifest；
boundary/cycles；
architecture/hygiene；
compile；
git diff --check。
```

## 15.2 Distribution

同步：

```text
active Field Encounter Wire；
旧Recall/Placement Wire状态；
Encounter Writer；
operation budgets；
single-session policy；
active profile；
legacy hidden Reader=false；
Core unchanged。
```

## 15.3 状态回填

更新：

```text
CURRENT_STATUS；
MODULE_PROGRESS_LEDGER；
ACTIVE_PROJECT；
实际推进向量；
全部模块实际完成度；
能力/限制；
最新HEAD；
最近验证Evidence；
下一候选动作。
```

## 15.4 能力名称

全部闭合允许：

```text
UNIFIED_FIELD_ENCOUNTER_READ_WRITE_DUALITY_VALIDATED_AT_<HEAD>
```

否则：

```text
AOLD_UNIFIED_FIELD_ENCOUNTER_IN_PROGRESS_AT_<HEAD>
```

不得写：

```text
读写性能已永久一致；
最终架构；
sealed；
100%；
全部Memory质量已验证。
```

---

# 16. Gate L：Final Gate 与 `AGENTS.md` 再验证

Final Gate 必须重新验证：

```powershell
$agents = Join-Path $PWD "AGENTS.md"

if (-not (Test-Path $agents)) {
    throw "AGENTS.md must exist."
}

if ((Get-Item $agents).Length -ne 0) {
    throw "AGENTS.md was rewritten after Gate 0."
}

$sha = (Get-FileHash $agents -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha -ne "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") {
    throw "AGENTS.md is not exactly empty."
}

$blob = (git hash-object AGENTS.md).Trim()
if ($blob -ne "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391") {
    throw "AGENTS.md Git blob is not empty."
}
```

Final Gate 必须满足：

```text
AGENTS.md zero-byte；
V3.12活动；
一套Field Encounter合同；
root结构操作中立；
事实/空位同Locality；
终态effect矩阵；
conditional commit；
主代理同run；
后台单Host session；
Cartographer child=0；
hidden Reader=0；
single-entry；
query/fact index=0；
内容资格分类=0；
Raw Capture不丢；
stale零写；
duplicate/orphan=0；
Manifest完整；
production violations=0；
production cycles=[]；
工作树clean；
完整历史Bundle验证通过。
```

---

# 17. 真实停止条件

只在以下情况停止：

```text
1. 现有Core无法提供任何合法vacancy候选且必须改变物理合同；
2. OpenClaw同一Host session无法在Formation后继续工具导航；
3. 主代理同run工具生命周期无法维持operation状态；
4. 统一合同会迫使query进入Python语义搜索；
5. conditional commit无法避免陈旧写入；
6. 旧数据迁移会损坏Raw Capture/Statement/Handle/Core；
7. 统一后必须multi-entry或外置索引才能正确工作；
8. 当前工作树存在无法识别且不能保全的用户修改。
```

普通问题直接修复继续：

```text
Prompt；
JSON；
tool schema；
测试；
命名；
预算；
性能；
文档；
Provider有限失败。
```

停止也必须：

```text
提交全部真实进展；
工作树clean；
生成完整Bundle；
如实标IN_PROGRESS；
不得补造Evidence。
```

---

# 18. 明确非目标

```text
Core物理参数修改；
multi-cell；
多物理层Placement；
Stitch最终合同；
多Chart；
Topic/Entity；
vector/graph/embedding；
query/fact索引；
multi-entry；
Provider更换；
模型训练；
PB规模；
正式发布；
History/Audit产品；
内容敏感性分类；
canonical redaction。
```

---

# 19. 建议提交序列

```text
chore(repo): clear root AGENTS execution overlay
checkpoint(aold): adopt unified Field Encounter V3.12
docs(architecture): map Recall and Placement assets into Encounter
feat(access): introduce operation-neutral Field Encounter contract
feat(access): project facts and legal vacancies in one Locality
feat(access): resolve Encounter terminals into recall and placement effects
fix(access): condition Encounter commits on current field state
feat(openclaw): use Field Encounter in the main agent run
feat(openclaw): continue proposition formation into Field Encounter
test(aold): validate read write and mixed Encounter matrices
validation(aold): compare dual-session and unified-session live paths
docs(aold): record unified Field Encounter capability
```

---

# 20. Evidence 与报告

生成：

```text
validation/aold_unified_field_encounter_20260728.jsonl
validation/aold_unified_field_encounter_summary_20260728.json
docs/project/AOLD_UNIFIED_FIELD_ENCOUNTER_REPORT.md
```

必须绑定：

```text
Git identity；
Host/Provider/model；
Capture；
Formation；
operation pages；
fact/vacancy cards；
semantic terminal；
effect；
commit状态；
session/tool counts；
old/new latency；
query/write/mixed；
restart/concurrency；
Manifest/boundary；
AGENTS empty SHA。
```

冻结：

```text
停止或旋转live Evidence输出；
记录exact bytes/lines/SHA；
commit；
Git blob复算；
不得交付后继续追加冻结文件。
```

---

# 21. Git Bundle

建议：

```text
nollm_aold_unified_field_encounter_20260728_<shorthead>.bundle
```

仓库外：

```powershell
git bundle create ..\nollm_aold_unified_field_encounter_20260728_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_unified_field_encounter_20260728_<shorthead>.bundle
Get-FileHash ..\nollm_aold_unified_field_encounter_20260728_<shorthead>.bundle -Algorithm SHA256
```

最终：

```text
所有修改已commit；
working tree clean；
bundle完整历史；
bundle verify通过；
只交一个Bundle。
```

---

# 22. 最终回复要求

最终只报告：

```text
branch / HEAD / commits；

AGENTS：
  exists；
  bytes=0；
  SHA-256；
  empty Git blob；

Architecture：
  Field Encounter Wire；
  root identity；
  fact/vacancy terminals；
  effect matrix；
  Core变化=0或实际偏差；

Read：
  relevant/NONE；
  hidden Reader；
  single-entry；
  query→visible；

Write：
  new/reuse/revision；
  local/junction/neutral vacancy；
  Host session数；
  Cartographer child数；
  Capture→commit；

Mixed：
  queries；
  recalled facts；
  pending effects；
  full Traversal count；

Engineering：
  tests；
  Manifest；
  boundary/cycles；
  actual vector/completion；
  limitations；

Bundle filename / SHA-256。
```

---

# 23. 最终任务概括

```text
Nollm不再先问：
  “我要读，还是我要写？”

它先进入场。

同一张Surface；
同一条路径；
同一个entry；
同一个Locality；
同时看到已有事实和合法空位。

遇到对应事实：
  Recall / Reuse / Revision。

遇到合法空位：
  有待写命题则Placement；
  没有则NONE。

读写只在终态分叉，
不在起点分叉。
```
