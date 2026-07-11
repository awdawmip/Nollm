"""Generate the complete M0 tracked-file ownership inventory."""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture" / "module-ownership"
CORE_NAMES = {"axial.py", "eisenstein.py", "cell_address.py", "coverage_template.py", "kernel_registry.py", "profiles.py", "fixed_point.py", "field_engine.py", "propagation.py", "bridge_kernel.py", "stitching.py", "geometry_storage.py"}
ACCESS_NAMES = {"capture.py", "admission.py", "admission_bridge.py", "placement.py", "placement_protocol.py", "facade.py", "host_contract.py", "openclaw_bridge.py", "evidence.py", "source_window.py", "real_sources.py", "ingestion.py"}
SNAPSHOT_NAMES = {"replay.py", "storage.py", "snapshot.py", "importers.py", "exporters.py", "json_canonical.py", "path_encoding.py"}
TRACE_NAMES = {"ledger.py", "recall_digest.py"}

FIELDS = ("path", "file_type", "current_namespace", "owner", "secondary_owner", "lifecycle_status", "runtime_role", "owned_state", "public_api", "imports", "imported_by", "migration_action", "confidence", "reason")

def tracked() -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    return [line for line in result.stdout.splitlines() if line]

def classify(path: str) -> tuple[str, str, str, str, str, str]:
    p = path.replace("\\", "/"); name = Path(p).name
    charter_owners = {
        "NOLLM_CORE_CHARTER.md": "CORE",
        "NOLLM_SNAPSHOT_CHARTER.md": "SNAPSHOT",
        "NOLLM_TRACE_CHARTER.md": "TRACE",
        "NOLLM_ACCESS_CHARTER.md": "ACCESS",
        "NOLLM_HISTORY_CHARTER.md": "HISTORY",
        "NOLLM_AUDIT_CHARTER.md": "AUDIT",
        "NOLLM_OPENCLAW_CHARTER.md": "OPENCLAW",
        "NOLLM_LAB_CHARTER.md": "LAB",
        "NOLLM_DISTRIBUTIONS_CHARTER.md": "DISTRIBUTION",
    }
    if p.startswith("docs/architecture/modules/") and name in charter_owners:
        return charter_owners[name], "ACTIVE", "KEEP", "HIGH", "current M0 module charter", "none"
    if p.startswith("docs/architecture/module-ownership/"):
        return "DISTRIBUTION", "GENERATED", "KEEP", "HIGH", "current M0 ownership governance record", "none"
    if p == "docs/delivery/NOLLM_M0_MODULE_OWNERSHIP_AND_MONOREPO_PACKAGE_SEPARATION_TASK_20260711.md":
        return "DISTRIBUTION", "ACTIVE", "KEEP", "HIGH", "authoritative M0 taskbook", "none"
    if p.startswith("docs/validation/M0_"):
        return "LAB", "ACTIVE", "KEEP", "HIGH", "current M0 validation record", "development-only results"
    if p in {
        "docs/project/M0_STARTING_STATE.md",
        "docs/project/NOLLM_CURRENT_STATUS.md",
        "docs/project/NOLLM_FUTURE_REPOSITORY_SPLIT_PLAN.md",
        "docs/project/NOLLM_REPOSITORY_COMPATIBILITY_MATRIX.md",
    }:
        return "DISTRIBUTION", "ACTIVE", "KEEP", "HIGH", "current M0 project governance", "none"
    if p.startswith("packages/nollm-core/"): return "CORE", "ACTIVE", "KEEP", "HIGH", "core package asset", "current geometry state"
    if p.startswith("packages/nollm-snapshot/"): return "SNAPSHOT", "ACTIVE", "KEEP", "HIGH", "snapshot package asset", "snapshot artifacts"
    if p.startswith("packages/nollm-trace/"): return "TRACE", "ACTIVE", "KEEP", "HIGH", "trace package asset", "observability events"
    if p.startswith("packages/nollm-access/"): return "ACCESS", "ACTIVE", "KEEP", "HIGH", "access package asset", "product decisions and handles"
    if p.startswith("packages/nollm-history/"): return "HISTORY", "CANDIDATE", "KEEP", "HIGH", "history package skeleton", "semantic history"
    if p.startswith("packages/nollm-audit/"): return "AUDIT", "CANDIDATE", "KEEP", "HIGH", "audit package skeleton", "audit records"
    if p.startswith("integrations/openclaw/"): return "OPENCLAW", "ACTIVE", "KEEP", "HIGH", "OpenClaw integration asset", "host/session/plugin state"
    if p.startswith(("experiments/", "lab/", "validation/", "reference/python/tests/", "examples/")): return "LAB", "ACTIVE", "MOVE" if p.startswith("experiments/") else "KEEP", "HIGH", "test, experiment, fixture, or benchmark", "development-only results"
    if p.startswith("distributions/"): return "DISTRIBUTION", "ACTIVE", "KEEP", "HIGH", "distribution composition metadata", "none"
    if p.startswith("legacy/"): return "LEGACY", "MIGRATION_ASSET", "QUARANTINE", "LOW", "preserved migration or historical asset", "historical"
    if p.startswith("reference/python/nollm/grf/"):
        if name == "relation_field.py": return "LEGACY", "BLOCKED", "DELETE_LATER", "HIGH", "external relation index is forbidden on the Core path and awaits M1 removal", "blocked relation index"
        if name in CORE_NAMES: return "CORE", "ACTIVE", "MOVE", "HIGH", "pure geometry/current-state implementation", "geometry current state"
        if name in ACCESS_NAMES: return "ACCESS", "BLOCKED", "SPLIT", "MEDIUM", "product/source/placement responsibility currently mixed with GRF", "access policy or source handles"
        if name in SNAPSHOT_NAMES: return "SNAPSHOT", "CANDIDATE", "SPLIT", "MEDIUM", "storage/replay responsibility requires public Core port", "snapshot or serialization state"
        if name in TRACE_NAMES: return "TRACE", "CANDIDATE", "SPLIT", "MEDIUM", "observability/recording responsibility", "trace records"
        return "LEGACY", "MIGRATION_ASSET", "QUARANTINE", "LOW", "mixed GRF responsibility pending extraction", "unknown or mixed"
    if p.startswith("reference/python/nollm/dream_geometry/"): return "LEGACY", "HISTORICAL", "QUARANTINE", "LOW", "pre-M0 V2 domain implementation retained for migration", "historical domain state"
    if p.startswith("reference/python/nollm/"): return "LEGACY", "HISTORICAL", "QUARANTINE", "LOW", "pre-modular root source retained pending M1 extraction", "historical or mixed runtime state"
    if p.startswith("protocol/"): return "ACCESS", "MIGRATION_ASSET", "SPLIT", "MEDIUM", "protocol mixes product and Core contracts", "wire contracts"
    if p.startswith("docs/delivery/") or "RECEIPT" in name: return "DISTRIBUTION", "HISTORICAL", "KEEP", "HIGH", "delivery history", "none"
    if p.startswith("docs/"): return "LEGACY", "HISTORICAL", "KEEP", "MEDIUM", "documentation requires current/superseded navigation", "none"
    if p.startswith("tools/"): return "LAB", "ACTIVE", "KEEP", "HIGH", "repository tooling", "development-only"
    if p.startswith("integrations/"): return "OPENCLAW", "MIGRATION_ASSET", "SPLIT", "MEDIUM", "host adapter integration", "host state"
    if p.startswith("cortex/"): return "ACCESS", "MIGRATION_ASSET", "QUARANTINE", "LOW", "product policy/cortex history", "product policy"
    return "DISTRIBUTION", "ACTIVE", "KEEP", "MEDIUM", "root repository governance or packaging asset", "none"

def imports_for(path: Path) -> list[str]:
    try: text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError): return []
    if path.suffix == ".py": return sorted(set(re.findall(r"^(?:from|import)\s+([A-Za-z0-9_\.]+)", text, re.M)))
    if path.suffix in {".ts", ".tsx", ".js", ".mjs", ".cjs"}: return sorted(set(re.findall(r"(?:from\s+|import\s*\()[\"']([^\"']+)", text)))
    return []

def main() -> None:
    paths = tracked(); import_map = {p: imports_for(ROOT / p) for p in paths}; reverse: dict[str, list[str]] = {p: [] for p in paths}
    for source, values in import_map.items():
        for target in paths:
            stem = target.removesuffix(".py").replace("/", ".")
            if any(value == stem or value.startswith(stem + ".") for value in values): reverse[target].append(source)
    rows = []
    for p in paths:
        owner, lifecycle, action, confidence, reason, state = classify(p); suffix = Path(p).suffix.lower().lstrip(".") or "none"
        rows.append({"path":p,"file_type":suffix,"current_namespace":str(Path(p).parent).replace("\\","/"),"owner":owner,"secondary_owner":"","lifecycle_status":lifecycle,"runtime_role":"production" if owner not in {"LAB","LEGACY","DISTRIBUTION"} else "development_or_reference","owned_state":state,"public_api":"candidate" if suffix in {"py","ts","js"} else "none","imports":";".join(import_map[p]),"imported_by":";".join(sorted(reverse[p])),"migration_action":action,"confidence":confidence,"reason":reason})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "MODULE_OWNERSHIP_MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    (OUT / "MODULE_OWNERSHIP_MANIFEST.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "UNCLASSIFIED_TRACKED_FILES.txt").write_text("", encoding="utf-8")
    print(f"classified {len(rows)} tracked files; unclassified=0")

if __name__ == "__main__": main()
