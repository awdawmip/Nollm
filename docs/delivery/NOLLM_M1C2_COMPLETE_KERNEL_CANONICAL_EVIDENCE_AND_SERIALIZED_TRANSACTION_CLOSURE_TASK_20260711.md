# Nollm M1-C2：完整 Kernel 合同、Canonical Evidence 与串行事务闭合任务书

**日期**：2026-07-11
**阶段编号**：M1-C2 — Complete Kernel / Canonical Evidence / Serialized Transaction Closure
**状态**：M1-C1 Bundle 系统审核未通过后的唯一闭合任务
**输入 Bundle**：`nollm_m1c1_exact_geometry_access_binding_state_closure_20260711_9018aeb1.bundle`
**输入 Bundle SHA-256**：`1391dedcc741fb2ac567f6051c7dfe069d5e8938ffd0feb5e17ddd0c7e877148`
**输入 HEAD**：`9018aeb18179f1a6db1efd7bec6bf1aabd2c5786`
**输入分支**：`codex/m1c1-exact-geometry-access-binding-state-closure`
**建议工作分支**：`codex/m1c2-complete-kernel-canonical-evidence-serialized-transaction`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 发现问题就地修复 + 最终单一 Git bundle
**阶段目标**：保留 M1/M1-C1 已建立的 Addressed Handle、模块边界、单一 current Evidence Binding 和基础回滚机制；补齐完整 Coverage/Kernel 合同，彻底闭合 Core/Access 文件真实性，并使 Access 异常原子性在同一进程并发调用下仍成立。

---

# 0. 外部审核结论与本任务定位

M1-C1 的工程成果应保留：

```text
完整 Bundle / Git 历史 = PASS
HEAD = 9018aeb18179f1a6db1efd7bec6bf1aabd2c5786
working tree = clean
production violations = 0
production cycles = []
nollm-core = 13 passed
nollm-snapshot = 3 passed
nollm-trace = 1 passed
nollm-access = 11 passed
M0 regression = 18 passed
architecture/no-forbidden/hygiene = 8 passed
geometry entry parity = 6/6
M1 E2E = PASS
GRF external Linux audit = 109 passed, 1 skipped
zstandard-dependent historical tests unavailable = 2
```

已实质完成：

```text
1. M1 Addressed Handle 和 package boundary 保留；
2. coverage_up=-1、coverage_down=+1 已恢复；
3. up/down entries 与旧 GRF 六个模板条目一致；
4. HandleBinding 已改为一个 Handle 一个 current_statement_id；
5. binding_missing / evidence_missing / evidence_payload_mismatch 已区分；
6. 顺序执行时，new/revision_current/revision_keep_history/forget 的普通 Binding 写失败可回滚；
7. Bare/Minimal 未恢复旧 GRF、OpenClaw Live、模型或 Corpus。
```

但当前不得输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

原因是以下五组正确性阻断仍存在：

```text
B1. Coverage parity 只比较 up/down 的 entry tuple；lateral、fanout、residual、profile/compiler metadata 和 registry identity 未迁移；
B2. Core 仍接受语义非 canonical 的 cell/atom/bridge 顺序和空 cell，导致 disk bytes != runtime state bytes；
B3. GeometryAnchor / BridgeSpec 等持久对象的直接构造仍可接受错误类型，Core 可写入随后无法 reopen 的状态；
B4. MemoryStatement / FileEvidenceStore 仍进行类型强转，且接受非 canonical、额外字段或错误类型的 Evidence 文件；
B5. Access 的跨 Core/Binding 回滚没有进程内事务锁，一个失败调用可撤销另一个已返回成功的调用。
```

此外，M1-C1 要求的升级版 E2E 实际只修改了 profile 名称，没有覆盖指定的完整负例和故障链。

M1-C2 只闭合这些问题。不得进入 M2、M3、真实模型或 OpenClaw Live。

---

# 1. 开工前最高约束

Codex 开始前必须依次读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. 根目录 AGENTS.md
3. docs/delivery/NOLLM_M1_CORE_HANDLE_ACCESS_COMMAND_EXTRACTION_AND_CYCLE_BREAK_TASK_20260711.md
4. docs/delivery/NOLLM_M1C1_EXACT_GEOMETRY_ACCESS_BINDING_AND_STATE_TRUTHFULNESS_CLOSURE_TASK_20260711.md
5. 本 M1-C2 任务书
6. docs/architecture/modules/NOLLM_CORE_CHARTER.md
7. docs/architecture/modules/NOLLM_ACCESS_CHARTER.md
8. docs/architecture/modules/NOLLM_SNAPSHOT_CHARTER.md
9. docs/architecture/modules/NOLLM_TRACE_CHARTER.md
```

必须更新并遵守根目录 `AGENTS.md`，至少加入：

```text
- Current stage is M1-C2 complete-kernel, canonical-Evidence, and serialized-transaction closure.
- Preserve M1/M1-C1 Addressed Handle, package boundaries, and one-current HandleBinding.
- Kernel parity must cover all three profiles and up/down/lateral, including residuals and fanout semantics.
- Geometry registry identity must bind every active relation-kernel semantic used by Recall.
- Any accepted Core state must re-encode byte-for-byte to the persisted bytes; semantic ordering differences and empty cells are invalid.
- Persistent public dataclasses must reject incorrect direct-constructor types before any write.
- MemoryStatement and Evidence files must never coerce numeric/bool/object values into strings.
- Access mutations must be serialized across Core and Binding snapshots/actions/rollback; one call may never roll back another successful call.
- Forget must remain possible by explicit Handle even when Evidence is missing; it must not depend on source-file availability.
- Do not proceed to M2, OpenClaw Live, model calls, corpus execution, or remote GitHub work.
```

## Gate 0 PASS

```text
第一性原理、M1、M1-C1、M1-C2 已读取；
AGENTS.md 已更新；
未恢复 graph/vector/embedding、外置关系索引、Python semantic placement、OpenClaw Live 或旧 Corpus；
未把本闭合任务扩展为 M2/M3。
```

---

# 2. 保全输入现场

从完整 Bundle 克隆，不得 reset、clean、改写历史或回退到 M0/M1 重新实施。

生成：

```text
docs/project/M1C2_STARTING_STATE.md
```

必须记录：

```text
input HEAD = 9018aeb18179f1a6db1efd7bec6bf1aabd2c5786
input bundle SHA-256 = 1391dedcc741fb2ac567f6051c7dfe069d5e8938ffd0feb5e17ddd0c7e877148
branch / status / log
package tests
M0 / architecture / GRF results
boundary report
本任务五组阻断及外部复现值
```

外部复现值至少写入：

```text
active KernelRegistry has no lateral template;
active lateral ring=2 returns 12 cells while retained GRF rejects fanout > 7;
MemoryStatement("s", 123) is accepted and reloads as "123";
noncanonical Evidence with extra fields and numeric context refs is accepted and coerced;
BridgeSpec with integer bridge_id/anchor_id is persisted but CoreRuntime reopen fails;
reversed canonical cell list is accepted yet disk bytes != runtime bytes;
empty cell is accepted then disappears from runtime;
concurrent failed Access transaction can erase another call that already returned success.
```

## Gate 1 PASS

```text
M0-C1、M1、M1-C1 提交链完整；
初始状态和外部阻断已保全；
工作树起点明确；
没有重新启动暂停任务。
```

---

# 3. Gate A：完整 Coverage / Kernel 合同迁移

## 3.1 当前不完整之处

当前活动 Core 只迁移了：

```text
profile_id
direction
entries(layer_delta,dq,dr,weight_q16)
up/down registry
```

尚未迁移：

```text
lateral registry template；
DEFAULT_FANOUT_LIMIT；
from_layer_mod / to_layer_mod；
source_phase；
sum_weight_q16；
normalization_residual_q16；
approximation_residual_q16；
compiler method / weight_format / flags / layer_index_direction；
完整 profile metadata；
上述语义进入 registry identity 的确定性绑定。
```

`dream_quasi_v1` 在旧权威合同中必须明确：

```text
normalization_residual_q16 = 0
approximation_residual_q16 > 0
method = symbolic_research_template_with_residual
flags includes boundary_ambiguous
```

不得以“Recall 当前未读取 residual”为理由删除已接受的 profile 合同。

## 3.2 恢复完整 Profile 合同

`nollm-core` 中的 Profile 至少包含并严格验证：

```text
profile_id
role
coordinate_model
scale_model
rotation_model
weight_format
runtime_polygon
runtime_float_allowed
description
```

必须保留：

```text
eisenstein_exact_v1
aligned_baseline_v1
dream_quasi_v1
```

Profile registry 必须有确定性 identity/digest，不能只依赖一个手写 version 字符串。

## 3.3 恢复完整 CoverageTemplate 合同

活动 `CoverageTemplate` 至少包含：

```text
profile_id
direction
from_layer_mod
to_layer_mod
source_phase
entries
sum_weight_q16
normalization_residual_q16
approximation_residual_q16
compiler metadata
```

活动 `KernelEntry` 至少包含：

```text
layer_delta
dq
dr
weight_q16
kernel_type
flags
```

所有 dataclass 的直接构造和 from_mapping（如提供）均须严格类型校验。

## 3.4 KernelRegistry 必须覆盖全部活动几何语义

对每个 profile 注册：

```text
coverage_up
coverage_down
lateral
```

要求：

```text
3 profiles x 3 directions = 9 active templates；
Recall 的 lateral 路径必须通过 KernelRegistry/CoverageTemplate，而不是绕过 registry 调独立 helper；
registry identity 必须包含 profile digest、9 templates、residual、flags、layer direction、fanout limit 和 compiler identity；
修改任一活动 kernel 语义必须改变 registry identity。
```

Bridge 仍由显式 `BridgeSpec` 管理，不得伪造为静态 relation index；但 state identity 必须明确哪些关系语义由 registry 绑定、哪些由持久 BridgeSpec 绑定。

## 3.5 Fanout 必须是硬边界

恢复或等价实现：

```text
DEFAULT_FANOUT_LIMIT = 7
```

至少满足：

```text
up/down/lateral template entries <= fanout limit；
ring=1 lateral 合法；
ring=2 在默认限制下 pre-expansion reject；
RecallBudget 不得允许先构造无限/巨大 lateral ring 再依赖 beam 截断；
所有 fanout 检查在分配大列表前完成；
max_lateral_ring 和 fanout_limit 的合同明确。
```

不得以“可信环境”为由允许无界内存展开。

## 3.6 Exact runtime 禁止浮点和 polygon

活动 exact path 源码和运行时继续禁止：

```text
float
math.sin / math.cos
polygon / shapely
伪向量
q//2 / q*2 heuristic scaling
```

允许整数除法仅用于明确的非语义工具，不得恢复旧简化 Coverage。

## 3.7 Full parity

升级：

```text
lab/nollm-lab/m1/run_geometry_parity.py
```

必须比较 9/9 模板的完整合同，而非只比较 entry tuple：

```text
profile_id / direction
from_layer_mod / to_layer_mod / source_phase
entries and ordering
sum_weight_q16
normalization_residual_q16
approximation_residual_q16
compiler method / flags / weight format / layer direction / fanout
expanded target cells and weights
negative coordinates
phase preservation
```

旧 GRF 仅作为 Lab parity oracle，不得进入活动 package import。

## Gate A PASS

```text
9/9 full kernel parity 通过；
lateral 进入 registry；
ring=2 默认 fanout 被拒绝；
dream_quasi residual/flags 完整；
registry identity 覆盖全部活动 kernel 语义；
exact runtime 无 float/polygon/sin/cos/heuristic scaling。
```

---

# 4. Gate B：Core semantic-canonical state 与严格公共对象

## 4.1 当前可复现错误

当前代码会接受：

```text
canonical JSON 但 cells 列表顺序反转；
canonical JSON 中的空 cell；
GeometryAnchor(anchor_id=123, ...);
BridgeSpec(bridge_id=456, ...)。
```

后果：

```text
reversed cells:
  import accepted
  store bytes preserve reversed order
  runtime.state_bytes() re-sorts
  disk bytes != runtime bytes

empty cell:
  file stores one cell
  runtime discards it
  disk bytes != runtime bytes

bad BridgeSpec:
  bridge_add succeeds and persists
  current process appears usable
  reopen fails with bridge_id must be a string
```

## 4.2 建立单一语义验证/规范化路径

不得只验证 JSON 键排序。必须建立一个单一函数或对象：

```text
decode strict document
→ validate all identities/types/invariants
→ build runtime objects
→ re-encode through authoritative _document/_encode
→ require re-encoded bytes == input bytes
```

此验证必须被以下路径共同使用：

```text
CoreRuntime initial reopen
CoreRuntime.import_state
Snapshot restore
FileCoreStateStore.read_document
FileCoreStateStore.write_bytes/write_document（如保持 public）
```

若 `FileCoreStateStore.write_bytes` 不应被外部直接调用，则将其降为明确 private/internal port；不得继续公开一个只验证 JSON 格式、不验证 Core 语义的写入口。

## 4.3 必须拒绝的状态

```text
非 canonical JSON bytes；
非 authoritative semantic order 的 cells；
非 authoritative semantic order 的 atoms；
非 authoritative semantic order 的 bridges；
空 cell；
重复 cell；
同 cell 重复 local_atom_id；
重复 bridge_id；
atom/local id mismatch；
unknown profile；
registry identity mismatch；
float/bool 坐标；
错误字段类型；
额外或缺失字段；
非法 UTF-8；
任何 decode 后 re-encode 不同的状态。
```

关于跨 cell 相同 `atom_id`：必须在 Core charter 和测试中明确它是允许的局部身份重复，还是应被拒绝；不得保持未定义状态。若允许，说明 `AtomHandle` 才是唯一定位；若拒绝，加入全局不变量，但不得建立关系索引。

## 4.4 严格公共持久对象

至少对下列对象的直接构造和 mapping decode 做 exact-type validation：

```text
GeometryAddress
MemoryAtom
AtomHandle
GeometryAnchor
BridgeSpec
CoverageTemplate
KernelEntry
Profile
```

要求：

```text
type(value) is str / int / bool 的精确合同；
bool 不得冒充 int；
anchor_id / bridge_id 必须非空字符串；
cells 必须是 tuple[GeometryAddress,...]；
任何 Core public operation 不得写入随后无法 reopen 的对象。
```

## 4.5 File/runtime/Snapshot 同一性

对任何接受状态，在以下时点必须满足：

```text
store.read_bytes() == runtime.state_bytes() == SnapshotService.create(runtime)
```

时点：

```text
初始化；
每次 batch；
import_state；
Snapshot restore；
reopen；
bridge add/remove；
move/replace/remove。
```

## Gate B 测试

必须新增至少：

```text
test_reversed_cells_rejected
test_reversed_atoms_rejected
test_reversed_bridges_rejected
test_empty_cell_rejected
test_bad_direct_bridge_types_rejected_before_write
test_bad_anchor_types_rejected_before_write
test_store_public_write_cannot_bypass_semantic_validation
test_reopen_and_snapshot_bytes_equal_for_every_accepted_mutation
```

## Gate B PASS

```text
不存在 disk/runtime semantic divergence；
不存在当前进程可写、重开失败的持久对象；
所有 accepted state 可严格重放；
File-first 事实源真实成立。
```

---

# 5. Gate C：Canonical MemoryStatement 与 Evidence 文件

## 5.1 当前可复现错误

当前：

```python
MemoryStatement("s", 123)
```

可以构造并写入：

```json
{"content_utf8":123,...}
```

读取时又通过 `str()` 变为：

```text
"123"
```

当前 `FileEvidenceStore.get_original()` 还会接受：

```text
非 canonical pretty JSON；
顶层 extra 字段；
statement extra/missing 字段；
context_refs 中的 int/bool；
并把 1 / True 强制变为 "1" / "True"。
```

这直接违反 Evidence-first：原始 Evidence 不能在读取时被“修复”成另一种内容。

## 5.2 MemoryStatement 严格合同

`MemoryStatement` 必须严格验证：

```text
statement_id: exact non-empty str
content_utf8: exact non-empty str
source_handle: null or exact non-empty str
context_refs: exact tuple[str,...]
context_refs 内元素 exact non-empty str
```

`from_mapping` 必须：

```text
要求 exact dict；
要求字段集合完全匹配；
不得调用 str()/int()；
不得默默补默认字段，除非 schema 明确版本化允许；
不得接受 list-of-pairs、Mapping 子类或错误嵌套类型来绕过合同。
```

## 5.3 Evidence 文件必须 canonical

`FileEvidenceStore.get_original()` 必须：

```text
读取原始 bytes；
严格 UTF-8 decode；
严格顶层字段集合；
严格 schema_version；
严格 MemoryStatement mapping；
重新 canonical encode；
要求 encoded bytes == original bytes；
验证 statement_id 与哈希路径请求一致。
```

必须拒绝：

```text
extra/missing fields；
pretty JSON / 非 canonical key/list order；
数字或 bool 代替字符串；
错误 context_refs 类型；
非法 UTF-8；
statement identity/path mismatch；
同 statement_id 不同原文覆盖。
```

## 5.4 Evidence immutability

在同一进程/同一 Store 实例中，capture 必须串行并保持：

```text
同 ID + 同 bytes：幂等；
同 ID + 不同 bytes：始终 FileExistsError；
不得因两个并发 capture 的 check-then-replace 形成 last-writer-wins。
```

不要求跨机器分布式锁；报告明确当前并发保证范围。

## 5.5 Forget 的 Evidence 前置条件纠正

当前全局 precheck 会导致：

```text
Evidence 文件缺失
→ explicit forget 被 FileNotFoundError 阻止
→ Core atom 和 Binding 永远无法清理
```

固定 action-specific 规则：

```text
new / reuse / revision_current / revision_keep_history / defer：按合同要求 Evidence 存在；
forget：只要求 explicit Handle 和合法 Binding，不要求 Evidence 文件仍存在；
stitch / unstitch：不要求 Evidence 文件；
forget 删除 Core + HandleBinding，Evidence 若存在默认保留，若缺失也可完成清理。
```

## Gate C 测试

至少新增：

```text
test_memory_statement_rejects_numeric_or_bool_fields
test_evidence_rejects_noncanonical_bytes
test_evidence_rejects_extra_or_missing_fields
test_evidence_rejects_numeric_context_refs
test_evidence_read_never_coerces_types
test_concurrent_same_id_different_content_never_last_writer_wins
test_forget_succeeds_when_evidence_file_is_missing
```

## Gate C PASS

```text
Evidence bytes 和返回对象完全同义；
不存在读取时类型强转；
不存在非 canonical Evidence 被接受；
Evidence 缺失不会阻止明确的 forget 清理。
```

---

# 6. Gate D：Access 进程内串行事务与完整故障矩阵

## 6.1 当前顺序回滚可保留

M1-C1 已证明在单线程顺序调用中：

```text
new
revision_current
revision_keep_history
forget
```

遇到普通 Binding write failure 时，Core/Binding bytes 可恢复。

不得删除这一基础。

## 6.2 当前并发错误

外部审核已确定性复现：

```text
T1:
  snapshot Core/Binding old state
  Core.put(A)
  block before Binding replace

T2:
  Core.put(B)
  Binding.put(B)
  returns success with handle B

T1:
  Binding failure
  rollback to its old snapshots

final:
  T2 already returned success
  B no longer exists in Core/Binding
```

当前 `_atomic()` 没有 Access-level 事务锁，Core 自身 `RLock` 只保护单次 Core operation，不能保护跨 Core/Binding 的 snapshot-action-rollback 整体。

## 6.3 事务锁要求

在 `AccessRuntime` 或等价协调器中建立进程内共享 `RLock`：

```text
lock scope:
  capture（涉及 Evidence immutable check/write）
  reuse Binding mutation
  new
  revision_current
  revision_keep_history
  forget
  读取/恢复 Core+Binding pre-state
  rollback
```

要求：

```text
同一 Access workspace 的所有 AccessRuntime 实例必须共享同一事务锁语义，不能每实例各自一把锁；
锁必须按 canonical workspace identity 获取；
不得与 Core Snapshot 锁形成反向 lock order；
明确固定 lock order，例如 Access workspace lock -> Core lock -> Binding/Evidence file lock；
不要求跨进程 crash transaction，但不得出现同进程成功调用被另一失败调用撤销。
```

若不支持多 AccessRuntime 实例共享，则必须限制构造器并机器验证一个 workspace 只能有一个 coordinator；不得在文档中默认单线程却不约束 API。

## 6.4 完整故障注入矩阵

对以下 action：

```text
new
revision_current
revision_keep_history
forget
reuse
```

覆盖：

```text
Core failure before commit；
Binding validation failure；
Binding write failure after Core command；
Core rollback failure；
Binding rollback failure；
两线程交错：一失败、一成功；
reopen after failure。
```

普通可恢复异常：

```text
Core bytes unchanged；
Binding bytes unchanged；
Evidence bytes unchanged；
reopen consistent；
无 orphan atom / stale binding / false success。
```

回滚本身失败：

```text
raise AccessConsistencyError；
不得覆盖原始异常上下文；
不得伪称普通 action failure；
报告明确需要人工恢复。
```

## Gate D PASS

```text
单线程和同进程并发下均不存在成功调用被其他回滚撤销；
异常原子性真实成立；
未引入数据库、Event Sourcing、Audit 链或分布式事务。
```

---

# 7. Gate E：Snapshot / Trace / Boundary 再验证

Gate A-D 完成后重新证明：

```text
Snapshot freeze 与 Core mutation 共用同一 Core lock；
Access workspace lock 与 Snapshot lock order 无死锁；
Snapshot bytes 绑定完整 profile/kernel registry identity；
restore 严格拒绝 semantic-noncanonical state；
NullTraceSink / MemoryTraceSink / FailingTraceSink / CompositeTraceSink 不改变结果；
Trace frontier 反映 registry lateral/up/down template，但不进入业务状态；
删除 Trace 文件不改变 Core/Evidence/Binding/Snapshot；
Bare/Minimal 不 import Legacy；
production violations = 0；
production cycles = []。
```

Boundary 报告必须说明：

```text
完整 9-template parity 已替代旧 GRF；
Legacy 仅作为 Lab oracle/compatibility；
zero-boundary 不是 lifecycle suppression；
active packages 使用最小 PYTHONPATH 可独立测试。
```

更新：

```text
docs/architecture/module-ownership/M1C2_BOUNDARY_CLOSURE.md
docs/architecture/module-ownership/M1C2_BOUNDARY_REPORT.json
```

## Gate E PASS

```text
精确完整 Kernel、严格 Evidence 和串行事务没有破坏模块边界、Snapshot 或 Trace。
```

---

# 8. Gate F：真正升级 M1-C2 E2E

M1-C1 的 `run_m1_minimal_e2e.py` 实际只将 profile 从 `exact` 改为 `eisenstein_exact_v1`，没有执行任务书指定的 M1-C1 负例和故障链。

现在必须真实升级：

```text
lab/nollm-lab/m1/run_m1_minimal_e2e.py
```

最小链至少包含：

```text
1. capture canonical Evidence；
2. explicit new；
3. exact coverage_up recall；
4. registered lateral ring=1 recall；
5. ring=2 fanout reject；
6. Evidence fallback；
7. reuse supporting statement 不替换 current；
8. revision_current 切换 current；
9. revision_keep_history；
10. Snapshot create；
11. move/bridge；
12. restore；
13. Recall/Evidence 回到快照；
14. FailingTraceSink parity；
15. 所有 mutating actions 的 Binding 故障回滚；
16. 两线程一成功一失败的 transaction serialization；
17. reversed cells / empty cell / bad BridgeSpec reject；
18. noncanonical Evidence / numeric Evidence reject；
19. unknown profile reject；
20. forget with missing Evidence succeeds；
21. defer 不写；
22. reopen bytes equality。
```

E2E 输出结构化 JSON，包含每个 Gate 的明确布尔事实；不得只输出一个总 `passed`。

更新报告：

```text
docs/validation/M1C2_COMPLETE_KERNEL_CANONICAL_EVIDENCE_TRANSACTION_REPORT.md
```

报告必须分开：

```text
外部可复现事实；
Windows 实际结果；
当前环境依赖失败；
并发保证范围；
process-crash 非目标；
Legacy parity 范围；
M2 前置条件。
```

不得把：

```text
6/6 entry parity
```

写成：

```text
完整几何 parity
```

必须报告：

```text
9/9 full template parity
```

及 residual/fanout/metadata 检查。

## Gate F PASS

```text
E2E 实际覆盖任务要求；
报告与代码、测试、环境完全一致；
不存在只改 fixture 名称却宣称闭合。
```

---

# 9. 独立 Package Gates

## Core

最小环境：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/packages/nollm-core/src"
python -m pytest -q packages/nollm-core/tests
```

必须新增或扩展：

```text
test_full_coverage_template_contract.py
test_lateral_registry_and_fanout.py
test_profile_registry_identity.py
test_kernel_registry_identity_completeness.py
test_core_semantic_canonical_state.py
test_public_persistent_object_strict_types.py
```

## Snapshot

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests
```

## Trace

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-trace/src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests
```

## Access

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-access/src"
) -join ";"
python -m pytest -q packages/nollm-access/tests
```

必须新增或扩展：

```text
test_memory_statement_strict_types.py
test_evidence_store_canonical_bytes.py
test_evidence_store_immutability.py
test_access_all_action_exception_atomicity.py
test_access_transaction_serialization.py
test_forget_without_evidence.py
```

新 package tests 不得加入：

```text
reference/python
integrations/openclaw
experiments/grf
```

完整 parity 只能在 Lab/compatibility gate 使用旧 GRF。

---

# 10. Final Gate

统一环境：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-trace/src",
  "$PWD/packages/nollm-access/src",
  "$PWD/packages/nollm-history/src",
  "$PWD/packages/nollm-audit/src",
  "$PWD/reference/python"
) -join ";"
```

执行：

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py --report docs/architecture/module-ownership/M1C2_BOUNDARY_REPORT.json

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests

python -m pytest -q reference/python/tests/m0
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py

python -m pytest -q reference/python/tests/grf
python lab/nollm-lab/m1/run_geometry_parity.py
python lab/nollm-lab/m1/run_m1_minimal_e2e.py

python -m compileall -q packages/nollm-core/src packages/nollm-snapshot/src packages/nollm-trace/src packages/nollm-access/src

git diff --check
git status --short
```

若外部环境仅缺 `zstandard`，允许精确排除：

```powershell
python -m pytest -q reference/python/tests/grf `
  --ignore=reference/python/tests/grf/test_grf7r2_evidence_pack.py `
  --ignore=reference/python/tests/grf/test_grf7r3_compact_evidence.py
```

必须记录完整 Windows 结果和外部可复现结果，不得把环境报告混写成同一次运行。

---

# 11. M1-C2 接受条件

只有全部满足，才可输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

条件：

```text
1. M1/M1-C1 Addressed Handle、package boundary、one-current Binding 保留；
2. 三个 profile 的 up/down/lateral 共 9 个完整模板进入活动 Core；
3. CoverageTemplate residual、flags、compiler metadata、phase/layer-mod 合同完整；
4. lateral 通过 KernelRegistry，不绕过 registry；
5. 默认 fanout 硬上限存在，ring=2 在默认限制下拒绝；
6. registry identity 覆盖完整 profile/kernel/fanout/residual 语义；
7. 9/9 full parity 通过；
8. exact runtime 无 float/polygon/sin/cos/heuristic scaling；
9. semantic-noncanonical list order 和空 cell 被拒绝；
10. accepted state 始终 disk == runtime == snapshot bytes；
11. GeometryAnchor/BridgeSpec 等直接错误类型在 pre-write 阶段拒绝；
12. 不存在写入成功但 reopen 失败的 Core state；
13. MemoryStatement 不做任何 str/int 强转；
14. Evidence 文件严格 canonical 且字段集合精确；
15. 非 canonical/额外字段/数字 context Evidence 被拒绝；
16. 同 ID 不同 Evidence 不会并发 last-writer-wins；
17. forget 在 Evidence 缺失时仍能按 explicit Handle 清理 Core/Binding；
18. Access 跨 Store 事务在同进程并发下串行；
19. 一个失败调用不会撤销另一个已成功返回的调用；
20. new/revision_current/revision_keep_history/forget/reuse 故障矩阵通过；
21. rollback failure 明确抛 AccessConsistencyError；
22. Snapshot/Trace/Boundary 回归通过；
23. production_violations = 0；
24. cycles_production = []；
25. Bare/Minimal 不引用 Legacy；
26. M0、架构、主要 GRF 回归保持；
27. M1-C2 E2E 实际覆盖完整正负链；
28. OpenClaw Live、模型、Corpus、远端拆仓未启动；
29. 所有改动已 commit；
30. 工作树干净；
31. 最终只交一个完整历史 Git bundle。
```

---

# 12. 明确非目标

M1-C2 不做：

```text
MemoryStatement Formation Corpus；
PlacementDecision Corpus；
真实 LLM；
OpenClaw Live；
语义质量评测；
History/Audit 产品化；
PB/1M 压测；
多进程/跨机器分布式事务；
数据库/Event Sourcing；
远端 GitHub 拆仓；
Graph/Vector/Embedding；
全局 relation index；
Evidence Capsule/Merkle/供应链安全。
```

---

# 13. 真实停止条件

只有以下情况可停止：

```text
1. 完整 retained CoverageTemplate 合同内部自相矛盾；
2. lateral/fanout 无法在不引入外置关系索引的条件下有界实现；
3. Core semantic canonical validation 无法在 Windows 文件语义下成立；
4. Evidence canonical/immutable 必须依赖数据库或重型事件系统；
5. Access 同进程事务串行必须修改 Core/Access 所有权方向；
6. 9/9 parity 暴露旧权威 fixture 本身冲突；
7. 需要真实 LLM/OpenClaw 才能验证基础合同；
8. 大规模环境故障无法定位。
```

不要因以下问题停止：

```text
文件名；
目录小调整；
测试数量增加；
需要重写 M1 E2E；
需要补充 strict dataclass validation；
需要增加 workspace lock registry；
旧 GRF 个别 fixture 需要薄 Lab adapter；
当前仍是单文件 Core/Binding/Evidence 状态。
```

---

# 14. 建议内部 Checkpoint

```text
Gate 0-1:
  docs(m1c2): record complete-kernel and state-truth blockers

Gate A:
  fix(m1c2): restore full profile coverage and lateral registry contracts

Gate B-C:
  fix(m1c2): enforce semantic canonical core and evidence files

Gate D:
  fix(m1c2): serialize access transactions and complete failure matrix

Gate E-F:
  test(m1c2): close snapshot trace boundary and full end-to-end validation
```

通过内部 Gate 后直接继续，不等待外部审查。

---

# 15. 最终交付

必须：

```text
所有修改 commit；
工作树干净；
Bundle 在仓库外生成；
Bundle 包含完整历史；
验证 Bundle；
文件名包含阶段和 HEAD 短哈希；
只交一个 Git bundle。
```

建议文件名：

```text
nollm_m1c2_complete_kernel_canonical_evidence_serialized_transaction_20260711_<shorthead>.bundle
```

最终回复提供：

```text
branch
HEAD
commit list
Gate A-F summary
9/9 full geometry parity
fanout negative result
semantic canonical state negative matrix
Evidence canonical negative matrix
all-action atomicity matrix
concurrency serialization result
package test counts
M0/architecture/GRF regression
production boundary count
production cycle count
known limitations
bundle filename
bundle SHA-256
```

不得声称：

```text
M2 已开始；
LLM Placement 已验证；
OpenClaw 已接入；
Memory Quality 已证明；
PB 级已完成；
History/Audit 已产品化；
多进程 crash transaction 已实现；
GitHub 已拆仓。
```

---

# 16. 一句话执行目标

> **在不改变 M1 模块边界和 Addressed Handle 主线的前提下，把 Coverage 从“六个 entry 对得上”推进为完整、受 registry identity 约束的九模板几何合同；把 Core、Evidence 和 Binding 的每一个接受字节都变成可重开、不可强转、不可并发回滚覆盖的真实事实源。**
