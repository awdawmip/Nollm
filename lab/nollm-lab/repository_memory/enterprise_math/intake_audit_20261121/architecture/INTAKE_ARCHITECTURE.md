# Nollm 新成果进入与研究中控台架构审查

日期：2026-11-21。范围：工程维护审查；没有创建 Researcher、Activity、CLAIM、正式科研 Task、Result 或 Review，没有操作调度器、线上部署或远端分支。

## 结论

现有实现已经提供可用的外部工作记忆：Host 读原文、形成理解、选择物理格保存；后续会话能从记忆取回理解，展开固定科学版本的原文，并显式修订。**它目前是由 Host 主动维护的研究理解场，没有在已审查的接入链中实现“每个新科学提交、Activity 或 Result 自动成为理解记忆”。** 这既不能被表述成已经自动吸收全部新成果，也不构成否定既有科学保存成功的理由。[原生形成/保存实现](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/research.py#L27-L61) · [适配器明确范围](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/README.md#L93-L106)

科学原文、记忆、Activity 关联和正式接纳具有不同的实际状态。Source 当前协议明确：科学文件经不可变提交、路径和完整内容回读核实后即可报告已保存；Activity、账户镜像、Result 和独立 Review 各据自身记录报告。补记直接引用同一科学证据，不应重新复制或重做已保存工作。[Source 保存协议](https://github.com/awdawmip/enterprise-math/blob/07fd94dcdc3765375d880d20fd22d122b2123037/docs/PORTABLE_RESEARCH_PROTOCOL.md#L7-L19) · [Activity 边界](https://github.com/awdawmip/enterprise-math/blob/07fd94dcdc3765375d880d20fd22d122b2123037/docs/RESEARCH_ACTIVITY_PROTOCOL.md#L3-L19)

本轮完成了一个小型、可合并的本地候选：补齐适用研究入口的可选记忆路由；明确 `current` 的实际含义；把已有有向连接与撤销原生 API 接到 MCP；增加基于既有 `CoreRuntime.bridges()` 的薄连接读取接口，用原连接 ID 查看不确定写入后的现状；补充实际读者需要的翻页方式和页宽 schema。没有建立新的成果治理系统、身份系统、源库扫描器或自动语义配对器。**本报告不宣称这些新增接口已经部署。**

## 1. 版本和证据范围

| 对象 | 本次读取的精确版本 | 可据此判断的范围 |
| --- | --- | --- |
| EM 科学/规则 Source | `07fd94dcdc3765375d880d20fd22d122b2123037` | AGENTS、startup、portable、Activity、架构、Driver 接纳边界 |
| GK 项目路由 | `286ad9e1f06e2b18ce71d4669ce31274f3a096e7` | 已由主执行核验的规范入口快照；本审查另读项目 index/bootstrap，按维护模式进入 |
| Python 后端 PR #112 | `282e4a06b4b08ccca8bf65d54b957bc43e52980f` | 当前导航候选代码；PR 明确 local candidate、live remains v23 |
| Nollm PR #7 | `34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766` | 当前原生研究适配器、连接、导航和语句存储模型 |
| 既有线上服务记录 | 后端 runtime `220d3c8f3b47ab62d137c6dc2868be55b501c7f3f92c29f8b4570ab4fe06e3d1`；Sites v23 | 来自主执行本轮实际状态读回及固定版本的已部署审计记录 |
| v23 网关源码 | `e9dc770e03f39132d8a3dd4ab5d5cd7be4f91d56` | 现有网关 initialize 已有 TASK/informed 使用与 FREE A 隔离说明；不能说所有入口都没有提示 |

[PR #112 当前元数据](https://github.com/awdawmip/em-research-mcp/pull/112) · [PR #7 当前元数据](https://github.com/awdawmip/Nollm/pull/7) · [固定版本线上审计](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/docs/evidence/nollm-memory-20261121/ONLINE_AUDIT.md)

本地读取的 v23 网关位于 `/workspace/scratch/4eeff3663e39/nollm_mcp_20261120/gateway/.sites-checkout/lib/em-gateway.mjs`，第 227 行为 initialize 说明；对应 `lib/research-memory-contract.mjs` 是五工具描述。该检视没有修改旧线上源码副本。新增网关候选及在线实测由主执行单独集成和记录。

下列“没有”结论限定在实际读取的 adapter、注册、同步器和启动协议调用链；不把全局关键词搜索未命中扩大成整个项目绝不存在其他实验。

## 2. 从科学原文到后续研究的实际路径

| 阶段 | 当前真实实现 | 谁作判断 | 尚未自动发生的事 |
| --- | --- | --- | --- |
| 科学 Source 已保存 | 现有 GitHub/Source 保存与固定内容回读；分支来源有效，但分支保存不自动等于 main 接纳 | 原作者及实际保存执行者 | 不因记忆尚未提炼或 Activity 尚未关联而撤销科学保存 |
| 形成理解 | `em_memory_source(reference=固定窗口)` 可直接读新材料；Host 写自然语言/公式正文与条件 | 当前 Host | 后端不调用模型，不自行提取新定理 |
| 写入与放置 | `em_memory_save` → `ResearchMemory.save` → `save_statement` → `MemoryStatement` + `AccessDecision` | Host 选择新理解和 `at=[q,r]`，或指定 `revise` | 事件、Result、Git commit 不会自行触发该调用 |
| 建立联系 | Nollm 已有 `stitch/unstitch`；原 backend 候选只有 `via=connected` 读取路径 | Host 明确选择方向和端点 | 没有自动证明跨线蕴涵；本地新补丁补齐 MCP 写和读接口 |
| 新会话发现 | 已知 ID 用 show；字面线索可 find；原生探索通过 Surface → 一个最终物理入口 → 邻域召回 | 新会话 Host 选择路径 | 索引命中、几何相邻或连接命中都不自动成为科学结论 |
| 回到科学原文 | `em_memory_source` 按保存的 commit/path/行范围，经既有材料读取器取得原文 | Host 核对需要的前提和证据 | 不用当前 main 静默替换旧科学版本 |
| 来源更新/局部修订 | 新 ID + `revise=旧当前ID` 保留旧文、固定旧来源并替换当前绑定 | Host 读新证据后作适用性判断 | `current=true` 不检测来源是否更新；桥仍附着物理格，需 Host 重审其意义 |
| 正式接纳 | 原有授权 Driver/Steward、任务语义、Result/Review 等按各自实际要求决定 | 实际有权角色与适用科学证据 | 记忆保存、Source 发布或 Task 发布不自行激活 Working Truth/Foundation |

对应实际代码位置：后端 [`src/research_memory.py:65–94`](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/src/research_memory.py#L65-L94)，材料读取与单场注册 [`src/em_mcp.py:411–431`](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/src/em_mcp.py#L411-L431)，Nollm [`enterprise_math/research.py:27–129`](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/research.py#L27-L129)。

## 3. Source 同步不等于新成果进入记忆

后端确实已有 `SourceSyncService`，并在应用生命周期内启动。它针对 `awdawmip/enterprise-math/main` 取只读 Git 数据，生成已有 guidance/projection 文件的不可变代际；`SOURCE_FILES` 由明确的 `BASE_SOURCE_FILES` 和 `PROJECTION_FILES` 组成。该列表包括 AGENTS、控制权威、Driver/continuation/portable/research method 和基础读取包，没有把每个 `research_notes`、Activity、Result 当成记忆输入。`tree()` 会取完整树元数据，但只选明确允许的文件集合。这不是新成果的理解抓取器。[`source_sync.py:20–45`](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/src/source_sync.py#L20-L45) · [`source_sync.py:160–181`](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/src/source_sync.py#L160-L181)

在这次接入的两份运行文件中，`memory` 只由五工具注册调用，保存唯一调用点是显式的 `em_memory_save`。`SourceSyncService` 没有调用 `ResearchMemory`、`save_statement` 或 `stitch`；Nollm README 又明确说明适配器不定期抓取或重排全库。因而可以得出有限且实用的结论：**现有中控台已同步部分规范资料，但没有由这一同步路径自动提炼和放置新研究理解。**

最小可执行做法是把“形成有复用价值的理解后保存”接到现有研究对话，而不使其成为科学保存的前置门槛。本地补丁这样做。以后若需要自动提醒遗漏的材料，可复用已有 Git 增量，给 Host 提供待提炼的来源定位；那仍应是候选输入，不能直接变成已理解、已审核的科学记忆。本轮没有实现此后续机制，也没有扩大为常驻扫描平台。

## 4. 记忆究竟保存了什么

原生 `MemoryStatement` 只有版本 ID、正文、主来源和其他引用；`describe` 返回正文、有序来源、是否仍有当前绑定以及 `revises`。它没有独立的科学接受等级、作者登记、证明条件或“截至最新主干”的字段。这是轻量模型，不应替它虚构已经具备的语义管理能力。[`MemoryStatement`](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/packages/nollm-access/src/nollm_access/statement.py#L6-L31)

需要保存的科学信息因此由 Host 的正文与实际来源承担：第一行作可辨识提要，正文保留命题、对象和作用域、关键条件、来源作者/贡献归属、证明或有限计算等真实证据性质、尚未复核或未决的范围。记忆作者的概括不能替换原作者贡献，也不能把工作理解重新标成已接纳定理。本地补丁把这一要求放在 `em_memory_save` 的说明和使用指南，没有增加必填状态表、额外审批或新身份记录。

`save_statement` 的 `source` 字符串由 Host 提供；后端检查固定提交与窗口形式，并在实际回源时使用既有材料读取器。它没有在每次保存时重复下载所有原文，也没有证明正文忠实于引用。这种分工符合内部可信组件的既定范围；研究者需要按问题保留真实条件，不能把接口成功当成数学验证。

### `current` 的准确含义

实际实现是 `FileHandleStore(field).exists(note_id)`。它回答“这个语句版本是否仍是该场的当前绑定”，并不回答“Source 有没有更新”“这条结论适用于新问题吗”或“是否已正式接纳”。原生 README 已明确此点，但此前 MCP 响应只有裸布尔值，工具描述也没有充分解释。[`describe:51–61`](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/research.py#L51-L61) · [README 的定义](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/README.md#L101-L104)

本地补丁保留 `current`，仅增加：

```json
{
  "current_scope": "working_memory_field",
  "source_freshness": "not_checked"
}
```

它不增加“latest Source”自动查询。测试实际证明：保存旧理解后读取一个更新的固定 Source，旧理解仍为 `current=true`；只有显式 revise 才改掉绑定。按旧科学输入开展工作时，这种固定引用仍是需要保留的正确行为。

## 5. 连接是物理格关系，维护时必须看两端条件

Nollm 的 `stitch(field, link_id, from_id, to_id)` 从两条当前笔记的句柄取物理地址，创建 `BridgeSpec`；连接单向。`connected` 的召回核最多允许一次 bridge 跳转，而 `local` 保持既有局部核。一个目标格可以含多条理解，所以命中远端目标的同时可能命中同格其他理解。[`research.py:74–115`](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/research.py#L74-L115)

这带来一个真实维护性质：同一命题原位修订后，桥仍指向同一物理格，后续召回会得到新版。它没有自动重新审核新旧命题的条件；不能从“桥仍在”推出跨线数学关系继续成立。Host 需据新证据保留、改变或撤销联系。本轮测试实际覆盖了 `remote → remote.v2` 后桥仍有效以及同格 peer 被召回，而没有把这一结构行为表述成数学迁移证明。

原 backend `282e4a0` 只公开五工具，即使 `walk(via="connected")` 已能消费桥，普通 MCP 会话仍不能创建或撤销它。原生代码已有两个动作，故最小补丁是直接映射，不引入外置关系索引。随后补上查看接口是实际使用所需：原来的 `walk.items[].via` 只包含核名，例如 `bridge`，并不包含具体 `link_id`，无法据此核对一次特定连接写入的结果。

### 本地候选三个接口

| 工具 | 输入 | 直接调用 | 输出及范围 |
| --- | --- | --- | --- |
| `em_memory_stitch` | 必需字符串 `link_id, from_id, to_id` | `research.stitch(field, ...)` | `{id, from:[layer,q,r], to:[layer,q,r]}` |
| `em_memory_unstitch` | 必需字符串 `link_id` | `research.unstitch(field, link_id)` | `{removed: link_id}` |
| `em_memory_links` | 可选 `link_id: string \| null = null` | 薄 `research.links(field, link_id)` → 既有 `CoreRuntime.bridges()` | 当前 `BridgeSpec.to_mapping()` 列表；无匹配 ID 则 `[]` |

写接口继续使用 `checkpoint:write` 和同一场锁；读接口使用 `source:read` 和同一锁。写操作清掉最近的导航页；它们不进入控制写队列。`links` 只读现存场，不初始化空场；返回原生的 `bridge_id`、from/to anchors、权重、class 和既有步数/fanout 参数。

连接写入或撤销的回执未知时，使用原 `link_id` 读取当前记录，核对存在性、方向和端点后消费实际状态。没有新增幂等账本或通用恢复层。测试验证了保存后存在、删后为空、按 ID 与全列表一致，以及查看前后 Core 文件字节未改变；没有将这些本地读回测试夸大为线上网络掉线注入。

## 6. 入口可发现性与正常研究使用

入口并非完全缺失。v23 Sites initialize 已明确 Nollm 用于 TASK/informed，普通记忆访问无需登记或 CLAIM，并说明 FREE A 使用原阶段入口。backend README、PR 说明和 Nollm 专用 README 也提供了真实调用办法。缺口更具体：canonical Python initialize、`em_context_manifest` 的适用研究路由，以及已读的 Source AGENTS/startup/portable/Activity 协议，没有把“可选复用—形成后保存—来源变化后修订”接成日常入口。[Python initialize](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/src/em_mcp.py#L374-L402) · [context manifest](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/src/em_mcp.py#L552-L603) · [Source startup 路线](https://github.com/awdawmip/enterprise-math/blob/07fd94dcdc3765375d880d20fd22d122b2123037/docs/RESEARCHER_STARTUP_CONTEXT_PROTOCOL.md#L83-L116)

本地补丁只在 Python initialize 和 `DIRECTED_RESEARCH`、`LINE_DRIVER` 的 context manifest 增加短路由：

- 已知笔记 ID：直接 `show`。
- 已知字面术语：辅助 `find`。
- 开放问题或邻域探索：`walk`，由 Host 选择原生入口。
- 要使用精确证据：按需要 `source`。
- 形成有复用价值的理解或修订：`save`，保留来源作者、科学状态和条件。

不会强制每次先经过几何菜单，不新增启动必读，也不对 `CONTROL_MAINTENANCE` 的 context manifest 主动开放成果场。FREE A、显式盲验证和 task-local 科学来源隔离继续适用。记忆入口的可用性不授予当前身份、共享写权限或数学接纳。

### 实际导航说明缺口

旧网关 walk 说明没有告诉读者翻页要把字面值 `"next"` 追加到完整 choices，也没有在 page_size 的 schema 中表达 1..8。主执行独立读者据此遇到了超范围页宽和绕路，具体在线回执由总报告保存。本地 Python 候选现在明确：`has_more=true` 时追加 `"next"`；page_size 可省略让运行库规划，显式范围为 1..8，并由现有 Pydantic `Field` 直接公开这一 schema，未叠加手工校验层。

同时明确 `pages_left` 是逻辑导航页预算；`budget_exhausted` 表示召回遍历被预算截断，不表示没有找到条目。几何规模试验中逻辑页数和实际 render 数可以不同；不能用前者冒充所有后端计算成本。这些说明帮助读者正确使用既有实现，没有把几何菜单当作研究权限检查。

## 7. 来源更新和正式接纳仍是独立问题

来源更新目前由 Host 触发：在相关新证据进入实际研究时读它，判断是同一理解的条件更新、另一条新命题，还是旧联系失效；随后分别 revise、新增或 unstitch。不是每次打开记忆都查整个库，也不是只要 main 前进就作废所有旧结论。冻结输入与当前控制规则在 Source 协议中原本就分开。[startup:103–106](https://github.com/awdawmip/enterprise-math/blob/07fd94dcdc3765375d880d20fd22d122b2123037/docs/RESEARCHER_STARTUP_CONTEXT_PROTOCOL.md#L103-L106)

对正式接纳，现有 Driver 合同规定 Working Truth 需要显式 Driver freeze 或确切任务语义，普通 Task 发布不足以激活；Driver 可以按问题需要接收、查看证据、修正、规划和保存，无须固定顺序、固定审核数量或先制造后继任务。声明独立审核或执行特权接纳时，仍应有真实独立性、作者贡献和适用权限。[Driver Working Truth](https://github.com/awdawmip/enterprise-math/blob/07fd94dcdc3765375d880d20fd22d122b2123037/docs/RESEARCH_DRIVER_OPERATING_CONTRACT.md#L175-L183) · [实际接纳与研究边界](https://github.com/awdawmip/enterprise-math/blob/07fd94dcdc3765375d880d20fd22d122b2123037/docs/RESEARCH_DRIVER_OPERATING_CONTRACT.md#L197-L203)

因此，报告一项新发现时应按实际证据分别说清：科学内容是否保存；可复用理解是否进记忆；Activity/镜像是否关联；是否存在实际审核或正式接纳。它们不是必须依次完成的新流程，更不能把缺少后两项写成“前面的科学没有保存”。

## 8. 候选、线上与可发现的版本

当前 PR 说明已区分 local candidate 和 v23，固定审计也记录了后端和 Nollm 运行版本。`em_status(identity_only=true)` 返回 activation manifest 的 runtime 标识；它不是一个自动对应 PR HEAD 的承诺。实际 `walk` 输出与工具目录能区分已加载的接口：主执行仍在既有线上观察到旧 walk 结构，而本地候选提供 `start/pages_left` 和 connected 参数。发布 GitHub 代码不使运行进程或长对话缓存自动升级。[候选记录](https://github.com/awdawmip/em-research-mcp/blob/282e4a06b4b08ccca8bf65d54b957bc43e52980f/docs/NOLLM_MEMORY_INTEGRATION_20261120.md#2026-11-21-研究导航候选)

下一次应用发布只需沿原维护方式配套这三部分：具体 Nollm 运行库、Python 后端、网关 schema/转发/说明，重开原持久场，并取得实际加载后的读写回执。保留已记录的版本对应即可；不需要再造内部验证哈希框架。本地候选不改科学 Source、既有工作场格式或调度规则。

## 9. 已完成补丁与验证

完整修改文件：

- `backend-candidate/src/research_memory.py`：show 语义、stitch/unstitch/links 直映、walk 翻页和页宽说明/schema。
- `backend-candidate/src/em_mcp.py`：两处可选研究路由，未改变控制权限或 Source 原文读取链。
- `backend-candidate/tests/test_research_memory.py`、`tests/test_service.py`：受影响目录和真实接口回归。
- `backend-candidate/docs/NOLLM_MEMORY_INTEGRATION_20261120.md`：科学/记忆/审核分层及本地候选说明。
- `nollm-candidate/lab/nollm-lab/repository_memory/enterprise_math/research.py`：八行薄 `links` public helper；对应 README 与现有 API 回归补充。

可直接应用的差异文件：`backend-intake-maintenance.patch` 基于 backend `282e4a0`；`nollm-links-read.patch` 基于 Nollm `34c16d1`。两份补丁均对精确原文件运行 `git apply --check` 通过。`memory-tools-candidate.json` 是当前真实 Python SDK 生成的八工具完整目录，供网关逐项复用；不是手写 schema 仿品。

主执行提供的 `../gateway-intake-candidate.patch` 基于 v23，已包含此前 walk 改动和本次 intake/links 改动，使用它时不再叠加旧 `gateway-walk-candidate.patch`。本审查快速读过其完整生产 diff 和 `../GATEWAY_VALIDATION.md`，未发现实质错接。现有网关通用整数验证只检查安全整数，1..8 的调用拒绝由后端 Pydantic 执行；schema 与说明已向调用方公开范围，不应把目录对比表述成另做了一层网关范围拒绝测试。

验证结果：

| 验证 | 结果 | 实际边界 |
| --- | --- | --- |
| 12 项 research memory + 1 项服务目录 | 13 PASS，`BACKEND_TESTS.txt` / `BACKEND_VALIDATION.json` | 真实 FastMCP/ASGI、真实 Nollm、临时工作场；原文网络沿现有明确 fixture |
| 连接性质 | PASS | 单向；目标同格 peer；源/目标原位修订；local 不变；撤销恢复；按 ID 查看；只读不改 Core 字节 |
| 既有权限/控制解耦 | PASS | 读取凭据可 links；无写权限拒绝两个写动作；记忆不构造 formal job engine，不建立控制目录 |
| 可选启动路由 | PASS | 实际 MCP 响应；Source bundle/projection I/O 被单独 fixture 替代，三 profile 保持原科学 pins、无权威授予、不打开场或扫来源 |
| Nollm 已安装 API | 1 PASS，`NOLLM_LINKS_VALIDATION.json` | 实际 install，调用各在独立进程；新增 links 读在写后/删后工作 |
| 网关 schema/relay | 主执行记录 16 PASS，`../GATEWAY_VALIDATION.md` | 本审查读过代码与记录；不重复计作独立重跑 |
| JavaScript → Python MCP → Nollm | 主执行记录 1 PASS，测试体约 49.1 秒 | 每次后端调用独立进程，共用临时场；来源网络 fixture，原生存储/连接/来源切片真实 |
| 真实线上加载新接口 | 本分工未执行 | 由主执行保存现有线上验证；此补丁仍是 candidate |

首次连接测试曾假设物理页一定展示目标笔记标题；同格 preview 被截断后触发 StopIteration。读取实际页确认该夹具只有一个物理候选，测试改为选择该唯一候选后通过。没有因此改变产品召回逻辑，也没有隐去这次失败。

测试依据的是精确当前的改动文件与当前 Nollm 核/适配器；本地 backend 其余测试依赖复用先前已用的局部源码副本。本报告没有声称执行完整 backend 仓库回归或所有生产集成。运行库候选位于 `architecture/runtime-candidate/scripts/runtime`，原 `native/runtime` 审计副本保持原版本。

## 10. 复现方式

先使用 GitHub connector 对上表固定 ref 读取对应文件，或检查本报告 `evidence/MANIFEST*.json` 中的原路径与 blob 元数据。实际审查选取的调用链可用以下局部命令重现，不需要遍历科学全库：

```sh
rg -n 'ResearchMemory|register_memory|memory|SourceSyncService' src/em_mcp.py src/research_memory.py src/source_sync.py
rg -n 'SOURCE_FILES|BASE_SOURCE_FILES|def tree' src/source_sync.py
rg -n 'save_statement|def describe|def stitch|def unstitch|def links' lab/nollm-lab/repository_memory/enterprise_math/research.py
```

在本次 backend 候选目录执行：

```sh
EM_NOLLM_RUNTIME=/workspace/scratch/4eeff3663e39/nollm_intake_audit_20261121/architecture/runtime-candidate/scripts/runtime \
  /workspace/scratch/4eeff3663e39/nollm_mcp_20261120/test-venv/bin/python -m pytest -q \
  tests/test_research_memory.py tests/test_service.py::test_initialize_and_inventory
```

在本次 Nollm 候选目录执行：

```sh
python3 -m unittest discover -s lab/nollm-lab/repository_memory -p test_enterprise_math_api.py
```

SDK 目录的生成使用 `em_mcp.build_server()` 与 `await server.list_tools()`，对 `em_memory_` 项调用 `model_dump(by_alias=True, exclude_none=True)`。生成时 STATE、control config 和 custody 均放在独立临时/禁用配置，不连接生产工作场。

科学效果、真实新成果入场后的独立新读者任务、以及网关候选的跨层验证由主执行汇总。这里的代码、规则和局部接口证据支持“当前链路怎样工作以及哪些具体缺口已修”，不支持尚未测得的总体科研收益结论。
