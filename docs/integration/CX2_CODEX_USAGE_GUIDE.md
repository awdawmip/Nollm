# CX2 Codex Usage Guide

本指南面向在 Nollm 仓库中执行 CX2 或后续验收任务的 Codex。核心规则是：先审查协议和基线，再把外部模型 proposal 转成 host review checklist；不得为了让 prompt 通过而修改 sealed module。

This guide is for Codex-style contributors working with the CX2 conformance pack.

## Start Checklist

1. Read `protocol/v2/CX2_CORTEX_ACTION_PLAN.md`.
2. Read `protocol/v2/CX2_EXTERNAL_MODEL_BOUNDARY.md`.
3. Confirm `main` already contains the accepted DG7-C1 commit.
4. Work only on the CX2 branch until acceptance.
5. Do not modify sealed production modules to make a prompt or plan pass.

## Translating External Proposals

外部模型输出必须先被拆成可审查清单。缺少 host-owned 输入时，Codex 应返回结构化缺口，而不是补造 proposal、placement、anchor 或 admission。

Turn external model text into a host review checklist:

- What is proposed for Capture?
- Which Promotion reason enum is claimed?
- Who owns the final decision?
- Which proposal and placement refs are missing?
- Which admitted IDs did the host explicitly declare?
- Which explicit workset bounds Recall?
- Which non-inferences are listed?

If any item is missing, return structured `need_from_host` instead of inventing it.

## Running Conformance

From the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPATH = "$PWD/reference/python"
python -m pytest -q reference/python/tests/test_cx2_cortex_action_plan.py reference/python/tests/test_cx2_cortex_plan_boundaries.py reference/python/tests/test_cx2_cortex_report_regeneration.py
python validation/cx2/run_cx2_conformance.py --output validation/cx2/CX2_EXTERNAL_CORTEX_INTEGRATION_CONFORMANCE_REPORT.md
```

The report runner writes only the explicit output path.

## Rejections

A rejected plan is not a system failure. It means the plan is outside CX2 boundaries. Report the stable reason code and the repairable message. Do not expose Python traceback or internal module paths.

## Delivery

Delivery requires:

- one CX2 integration commit;
- clean worktree;
- fixed validation commands;
- complete-history Git bundle outside the repository;
- `git bundle verify`;
- `git fsck --no-reflogs --connectivity-only`.

CX2 completion does not merge CX2 into `main`.
