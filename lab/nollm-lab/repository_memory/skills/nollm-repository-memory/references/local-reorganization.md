# 局部重组与存放

## 从实际观察编写计划

沿普通 `encounter` 选择一个物理入口，读取完整正文和来源。准备新增或搬移时，
在同一会话加 `--prepare-write` 观察候选；按需下降或返回。会话保留已观察事实的
物理 handle、候选格和实际观察路径，不保存另一份正文或长期分类索引。

Host 决定哪些判断需要改变，以及新位置是否便于以后阅读。先读证据再编写计划。
下面是格式示例，其中版本 ID、候选、路径和来源必须替换为本次真实观察与已读来源：

```json
{
  "schema_version": "nollm_local_reorganization_v1",
  "changes": [
    {
      "action": "revise",
      "target": "overview.v1",
      "id": "overview.v2",
      "text": "上层保存完整短判断，细节沿覆盖展开。",
      "sources": ["FULL_COMMIT:docs/design.md#L10-L20"]
    },
    {
      "action": "move",
      "target": "detail.v1",
      "to": "cell:0:1:0"
    }
  ],
  "readback": [
    {"id": "detail.v1", "path": [[-2, 0, 0], [-1, 0, 0], [0, 1, 0]]}
  ]
}
```

```sh
python3 "$cli" project --field "$field" encounter \
  --cursor-file "$session" --reorganize plan.json
```

| action | target | 其他字段 | 作用 |
| --- | --- | --- | --- |
| `new` | 已准备的 `cell:L:q:r` | `id,text,sources` | 放入独立判断 |
| `revise` | 已观察的当前表达 ID | `id,text,sources` | 原位更新当前判断，保留历史 |
| `reuse` | 已观察的当前表达 ID | `id,text,sources` | 保存支持表达，复用占用 |
| `move` | 已观察的当前表达 ID | `to` 为已准备的格 | 改变位置，正文和支持不变 |
| `forget` | 已观察的当前表达 ID | 无 | 退出当前占用，原表达继续可读 |

动作依次解释；后续动作可引用本批新建或修订后的当前 ID。`reason` 可写实际理由。
支持表达不会成为当前 ID。源字段直接保存固定的 `完整提交:path#Lfirst-Llast`，
也可以使用项目允许且确实阅读过的其他来源引用；CLI 不替 Host 核实正文是否被证据支持。

## 最终容量和回读

预算检查本批完成后的布局，因此满格可一次新增提炼后的判断、撤下原占用，
不必临时放宽容量。修订、移动和新增都计入最终正文；支持表达不重复计入当前正文。
预检失败不捕获新表达。预检成功后捕获的表达即使提交随后失败，也保留为可读 Evidence。

改变的当前表达自动要求一条从已观察 Surface 入口到最终位置的实际相邻
`coverage_down` 路径。会话路径足够时直接复用，否则用 `readback` 明确提供。
程序会检查每一条物理边，并在提交后读取终点当前表达。需要保留多个旧入口时，
可以为同一 ID 列多条路径；入口须在本次已观察的最终 Surface 层中。

这项检查覆盖改变的当前表达和显式列出的路径。它不证明全场无孤儿，也不证明
另一个模型会在有限预算内选到这些入口。后继模型的实际阅读仍需独立试用。
向上支撑与向下覆盖不是同一条关系，不能把有支撑当作从这个入口可读。

## 一起更新表层和容量

计划可带 `encounter` 部分配置以及完整 `content_budget`。后者使用现有
`nollm_access_content_budget_v1` 格式：`profile_id`、`chart_id` 和按物理层号的
`layers`。每层可配置 `max_cell_atoms`、`max_cell_utf8_bytes`，以及可选的
`max_layer_cells`、`max_layer_utf8_bytes`。这些限制算 UTF-8 字节和当前占用。

更粗表层需要 Host 先观察并准备其物理格，写入有意义的短判断；计划中再将
`encounter.surface_layers` 切到该层，扩展 `encounter.layers` 并提供对应预算。
新入口必须保有当前判断，改变的细节仍需能从最终入口向下读回。
预算和入口配置与这批 Core／绑定变更共用局部恢复记录。

普通异常恢复原布局和配置；进程中断后，下次打开 Access 先恢复未完成批次。
失败时会话保留，可检查错误再重试。同一版本 ID 已捕获时，重试须保持其正文和来源；
需要改变内容就用新版本 ID。成功返回 `commit_state: committed` 后会话删除。
这是 Access 打开时的恢复保证，独立直接读取 Core 的其他进程不获得跨文件瞬时事务视图。

## 显式切换物理分页

```sh
python3 "$cli" project --field "$field" storage
python3 "$cli" project --field "$field" storage --enable-paged --partition-width 64
```

第一条只读两份存储入口，不打开运行时或触发恢复。第二条显式迁移 Core 和绑定，
以后打开同一场自动使用分页。分页按 profile、chart、phase、物理层和坐标分区定位；
它不增加语义索引，不改变几何、正文、handle 或来源。

迁移依次处理两部分。若第二部分失败，结果为 `status: partial`、非零退出码，
并说明成功和失败的组件；重复同一命令即可继续。不要把部分成功当作两部分都完成。
已分页的组件再次执行不重排分区；改变宽度不是本命令的重分区功能。

已知格的读取与普通新写入只涉及其物理页；同页其他正文仍计入页成本。
Surface 读取指定入口层的占用元数据和本页表达。只知道 Statement ID 时寻找其当前
位置仍可能盘点所有绑定；完整快照也仍读取全状态。分页不消除这些明确的全量操作。
