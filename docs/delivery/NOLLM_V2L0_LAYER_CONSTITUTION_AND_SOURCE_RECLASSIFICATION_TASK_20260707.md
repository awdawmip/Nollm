# Nollm V2L0：Core→Terminal 分层宪法与源码重分类任务书

**日期**：2026-07-07
**阶段**：V2L0 — Layer Constitution / Source Reclassification
**活动基线**：`8bb324a3a5de46bebb6eadd217820627a971e2a0`
**已接受、未提升组件**：HAG1-C1R `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`
**建议工作分支**：`codex/v2l0-layer-constitution-source-reclassification`
**执行主体**：单一执行主体；禁止使用子代理、并行代理或后台任务。
**交付**：一个 complete-history Git bundle + 绑定 final head 的 parentless TQ1 evidence capsule。
**本阶段不做**：不合并 HAG1-C1R、不提升 HAG、不删除 V1/MT1/OpenClaw/prototype 文件、不启动任何 runtime。

---

## 0. 背景与唯一目标

Nollm 已明确采用两套正交视图：

```text
纵向业务路径：
Capture / Admission / Assembly

横向依赖层：
L0 Constitution
L1 Evidence and Identity
L2 Deterministic Domain Services
L3 Core Workflow
L4 Host Contract and Execution Bridge
L5 Host Adapter
L6 Terminal and Product
```

V2.1 已定义 Capture / Admission / Assembly 的对象语义、权限与成本边界。V2.2 已定义 Core 向外扩张、不同组件独立更新的分层架构。

本阶段只将这些项目级规则写入当前 V2 active source tree，并建立最小 import/document firewall。它是**重分类和导航闭合**，不是 V1 物理删除，也不是 HAG/ OpenClaw 实现。

唯一目标：

```text
让任何后续执行者从 repository root 开始，就只能得到：
V2 是唯一活动架构；
Core 不认识终端；
Adapter 不拥有事实；
Terminal 不绕过 contract；
OpenClaw 是 future L5/L6 migration asset；
V1 / MT1 / pre-V2 prototype 是 retired history，不是活动依赖。
```

---

## 1. 不可变架构结论

### 1.1 活动架构

```text
L0 Constitution and Protocol
L1 Evidence and Identity Kernel
L2 Deterministic Domain Services
L3 Core Workflow
L4 Host Contract and Execution Bridge
L5 Host Adapter Family
L6 Terminal and Product
```

依赖只允许从外向内：

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

### 1.2 三条业务路径

```text
Capture:
  explicit content -> CI1 -> DreamShard / CaptureReceipt

Admission:
  explicit candidate + decision + growth + placement
  -> BA1 -> DA1 -> AdmissionRecord

Assembly / Recall:
  explicit admitted workset + query
  -> DF1 -> DR1 -> DI1
```

Capture / Admission / Assembly 是业务路径，不是产品层。

### 1.3 OpenClaw 的正确位置

```text
OpenClaw:
  future L5 Adapter + L6 Terminal direction.

Old OpenClaw assets:
  frozen migration assets.

OpenClaw must not:
  be imported by V2 Core;
  own DreamShard;
  use legacy memory-core as V2 fact source;
  perform terminal-local auto-admission;
  treat cache as evidence;
  bypass HCG/HAG/HX1 public boundaries.
```

### 1.4 HAG1-C1R 的位置

```text
HAG1-C1R:
  accepted L5 File Admission Adapter component;
  unpromoted;
  not to be merged or modified in V2L0.
```

V2L0 must not use HAG code as a reason to alter CX2, HX1, CI1, BA1 or DA1.

---

## 2. Start conditions and branch discipline

Before any change:

```powershell
git status --short
git rev-parse main
git rev-parse origin/main
git show --no-patch --format='%H %s' 8bb324a3a5de46bebb6eadd217820627a971e2a0
git branch --show-current
```

Required:

```text
- local main must resolve to 8bb324a...;
- working tree must be clean;
- no fetch / pull / push;
- new V2L0 branch must start at local main;
- HAG branch and its evidence ref must remain unchanged;
- no reset / rebase / squash / cherry-pick;
- no local main promotion in this task.
```

If local main is not `8bb324a...`, stop and report exact refs. Do not infer remote truth from bundle data.

---

## 3. Sealed baselines and forbidden changes

Sealed production modules:

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

Forbidden:

```text
- changes under reference/python/nollm/dream_geometry/**;
- changes to HCG/HAG/HX1 implementation, public schema or tests;
- changes to TQ1 runner, packager or verifier;
- moving/deleting V1, MT1, OpenClaw or prototype source in this phase;
- changing pyproject/package identity;
- activation of OpenClaw/runtime/network/daemon/database/cache;
- adding V1 compatibility logic to V2;
- adding any terminal-specific condition to Core;
- main promotion;
- any remote operation;
- subagents.
```

---

## 4. Allowed paths

Only these paths may be modified or added:

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
validation/v2l0/V2L0_FIXED_GATE_RECEIPT.md

reference/python/tests/test_v2l0_layer_constitution.py
reference/python/tests/test_v2l0_source_reclassification.py

reference/python/tests/test_architecture_language.py
reference/python/tests/test_terminology.py
reference/python/tests/test_repository_hygiene.py
reference/python/tests/test_no_forbidden_features.py
reference/python/tests/test_package_hygiene_script.py
reference/python/tests/test_run_tests_runner.py

ROADMAP.md
AGENTS.md
```

The six pre-existing generic tests may be changed only when necessary to remove an explicit V1-current assertion and replace it with a stronger V2.2 assertion. Do not delete, skip, xfail or weaken them.

If any other test blocks V2L0 solely because it enforces V1 as active, stop and report its exact assertion before expanding scope.

---

## 5. Required content

### 5.1 `protocol/v2/LAYER_CONSTITUTION.md`

Create a concise normative document containing:

```text
- L0–L6 definitions;
- one-way dependency rule;
- distinction between layers and Capture/Admission/Assembly paths;
- object authority:
  Core owns facts, Adapter translates, Terminal presents;
- real identity vs host request ID vs terminal message ID vs CX2 projection ref;
- independent versioning and compatibility declarations;
- forbidden inward dependencies;
- OpenClaw migration boundary;
- HCG1/HAG1 location at L5, HX1/CX2 location at L4;
- DC1 compiler vs external Cortex policy naming distinction.
```

It must not restate or modify sealed lower-module algorithms.

### 5.2 Root navigation rewrite

Rewrite `README.md`, `ARCHITECTURE.md`, `ROADMAP.md` and `AGENTS.md` so they declare:

```text
- V2 is the only active architecture;
- V1, MT1 and pre-V2 prototypes are retired history;
- legacy source still physically present during staged cleanup is not an active API;
- OpenClaw is a frozen migration asset toward L5/L6, not deleted and not current runtime;
- HCG1 is accepted L5 File Capture Adapter;
- HAG1-C1R is accepted/unpromoted L5 File Admission Adapter;
- all main promotion and remote status must be rechecked on the actual machine;
- no terminal can bypass Host Contract / Bridge;
- no Core component may import terminal or adapter code.
```

Remove or supersede phrases equivalent to:

```text
stable V1 runtime
V2 parallel / not yet replacing V1
current architecture (V1 legacy state)
OpenClaw provider is current Nollm memory core
```

Do not claim HAG is main, OpenClaw is V2 integrated, or automatic admission is authorized.

### 5.3 Historical / migration records

Create:

```text
docs/history/V1_RETIREMENT_RECORD.md
docs/history/OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md
```

V1 retirement record must state:

```text
- V1 notebook/Card/Anchor/CLI/tool surface is historical;
- Git history is the canonical full archive;
- physical deletion/move occurs only in later U1/U2/U3 phases;
- no V1 compatibility imports may enter V2 Core;
- early anchor/honeycomb philosophy may remain research history,
  but must not silently define current API contracts.
```

OpenClaw record must distinguish:

```text
retained migration assets:
  hooks, session/context mapping, installer/configuration,
  idempotency, rollback, privacy redaction, compatibility probes, fixtures.

frozen legacy semantics:
  V1 Card/Anchor store, legacy memory-core delegation,
  native store as truth, global lexical search,
  terminal-local promotion, plugin cache as evidence,
  old geometry navigation as current recall.
```

### 5.4 Source topology and progress

Create/refresh:

```text
docs/project/NOLLM_SOURCE_TOPOLOGY_V2.md
docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md
docs/architecture/NOLLM_PROJECT_BOOK_V2_2_LAYERED_CORE_TO_TERMINAL.md
```

They must state:

```text
accepted main baseline: 8bb324a...
accepted but unpromoted HAG1-C1R: 0e0d21...
V2L0: current candidate work
```

Use exact status vocabulary:

```text
sealed
accepted
accepted / unpromoted
baseline
candidate
blocked
planned
deferred
historical
migration asset
```

Do not call V1 stable, HAG main, old OpenClaw V2 adapter, or bundle `origin/main` a live remote fact.

### 5.5 `protocol/v2/LEGACY_BOUNDARY.md`

Rewrite to make the distinction precise:

```text
V1 / MT1 / prototype:
  retired from active architecture; not production dependencies.

OpenClaw legacy:
  frozen migration asset; may be read for host behavior redesign only.

Physical source cleanup:
  later staged task; not V2L0.

No active Core import:
  dream_geometry must not import top-level legacy V1 modules,
  integrations.openclaw legacy modules, or terminal code.
```

---

## 6. Required tests

Add exactly two V2L0 tests plus disciplined updates to permitted generic tests.

### V2L0-01: normative layer constitution test

Assert the existence and required claims of:

```text
protocol/v2/LAYER_CONSTITUTION.md
V2.2 project book
component progress table
V1 retirement record
OpenClaw migration record
```

Assertions must confirm:

```text
L0–L6 exists;
dependency arrows are outside-in;
Capture/Admission/Assembly are explicitly called business paths;
HCG1/HAG1 are L5;
HX1/CX2 are L4;
OpenClaw is migration asset / future L5-L6;
real evidence identity != CX2 plan ref;
V2 is only active architecture.
```

### V2L0-02: static import firewall

Using AST or a minimal lexical import parser, inspect only:

```text
reference/python/nollm/dream_geometry/**/*.py
```

Reject imports of:

```text
nollm.cli
nollm.tool_api
nollm.openclaw_
nollm.companion_
nollm.archive
nollm.legacy_
nollm.native_field
integrations.openclaw
```

Allow existing internal `dream_geometry` dependencies exactly as sealed dependency rules permit.

This test does not enforce physical legacy deletion. It proves only that V2 Core remains terminal-independent.

### Generic-test rules

Any modified generic test must replace a V1-current assertion with a V2.2-current assertion. Required coverage must remain explicit:

```text
- no root document calls V1 active/stable/current;
- active protocol root is protocol/v2;
- no V2 Core source imports OpenClaw or V1 notebook runtime;
- HCG/HAG are not registered on V1 CLI/tool surface;
- legacy assets are documented as migration/history, not silently hidden.
```

---

## 7. Mandatory gates

Set:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"
```

Run:

```powershell
python -m pytest -q `
  reference/python/tests/test_v2l0_layer_constitution.py `
  reference/python/tests/test_v2l0_source_reclassification.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_terminology.py `
  reference/python/tests/test_repository_hygiene.py `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_package_hygiene_script.py `
  reference/python/tests/test_run_tests_runner.py
```

Then run public V2 regression:

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

HAG tests are not included in V2L0 acceptance because HAG is an accepted-but-unintegrated L5 component. It must remain unchanged.

Finally:

```powershell
git diff --check
git status --short
```

---

## 8. Final code and delivery

After gates pass:

```powershell
git add -- <allowed paths only>
git commit -m "docs(v2): establish core-to-terminal layer constitution"
$finalHead = git rev-parse HEAD
git status --short
```

Then execute a fresh final-head TQ1 C7R matrix:

```powershell
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$finalHead\v2l0"
$worktreeRoot = "C:\Users\chaos\nollm_test_worktrees\$finalHead"

python reference/python/scripts/run_nollm_test_matrix.py plan `
  --repo-root . `
  --receipt-root $receiptRoot `
  --target-node-count 120 `
  --max-shards 24 `
  --timeout-seconds 3600

python reference/python/scripts/run_nollm_test_matrix.py run-shard `
  --repo-root . `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot `
  --all `
  --workers 4 `
  --timeout-seconds 3600

python reference/python/scripts/run_nollm_test_matrix.py verify `
  --repo-root . `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot
```

Required matrix facts:

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

Build a new parentless evidence ref:

```text
refs/nollm-delivery/tq1-c7r/<finalHead>
```

Capsule must contain final matrix artifacts plus raw V2L0 targeted gate and V2 regression gate logs. It may use the sealed TQ1 governance format; the V2L0 taskbook itself must be committed as normal code history under `docs/delivery/` or `docs/project/` before final matrix, not forced into the sealed TQ1 governance filter.

Fresh checkout:

```powershell
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref `
  --repo-root . `
  --evidence-ref refs/nollm-delivery/tq1-c7r/$finalHead `
  --expected-head $finalHead
```

One complete-history bundle only:

```powershell
$bundle = "C:\Users\chaos\nollm_v2l0_layer_constitution_source_reclassification_20260707_<short-head>.bundle"
git bundle create $bundle --all
git bundle verify $bundle
git fsck --full
git diff --check 8bb324a3a5de46bebb6eadd217820627a971e2a0..$finalHead
Get-FileHash $bundle -Algorithm SHA256
```

Do not promote main. Do not push.

---

## 9. Stop conditions

Stop and report rather than broadening scope if:

```text
- local main is not 8bb324a...;
- any sealed production path or test requires modification;
- generic tests outside the explicit allowlist must be changed;
- V2 Core currently imports a legacy/terminal module and fixing it would require sealed-module edits;
- root documents cannot be reconciled without claiming unimplemented runtime behavior;
- a required gate has a real assertion failure;
- final matrix/evidence semantic verification fails;
- a code move/delete becomes necessary;
- HAG branch/evidence must be changed;
- any remote operation, runtime activation or subagent is needed.
```

---

## 10. Completion statement

V2L0 completion means only:

> Nollm’s active documentation, source topology and static firewall now describe a single V2 architecture that expands from Core through Workflow and Host Contract to independent Adapters and Terminals. V1/MT1/prototype code is classified as historical pending staged retirement. OpenClaw is retained as a frozen L5/L6 migration asset. No Core behavior, terminal runtime or HAG integration has been changed.

It does not mean:

```text
V1 files are already deleted;
OpenClaw is integrated;
HAG is promoted;
automatic admission exists;
global recall exists;
any terminal can bypass HX1;
main has moved.
```
