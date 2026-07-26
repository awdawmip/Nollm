"""Generate or verify the evidence-based module ownership manifest."""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture" / "module-ownership"
MANIFEST_JSON = OUT / "MODULE_OWNERSHIP_MANIFEST.json"
MANIFEST_CSV = OUT / "MODULE_OWNERSHIP_MANIFEST.csv"
UNCLASSIFIED = OUT / "UNCLASSIFIED_TRACKED_FILES.txt"
REVIEWED_AT = "2026-07-12"
ACTIVE_BASIS = "docs/project/ACTIVE_PROJECT.md"

FIELDS = (
    "path",
    "file_type",
    "current_namespace",
    "owner",
    "secondary_owner",
    "lifecycle_status",
    "asset_class",
    "validation_gate",
    "runtime_role",
    "owned_state",
    "public_api",
    "imports",
    "imported_by",
    "migration_action",
    "confidence",
    "reason",
    "target_path",
    "migration_status",
    "classification_evidence",
    "forbidden_feature_evidence",
    "review_status",
    "reviewed_at",
)

CORE_LEAVES = {
    "axial.py",
    "bridge_kernel.py",
    "cell_address.py",
    "coverage_template.py",
    "eisenstein.py",
    "fixed_point.py",
    "json_canonical.py",
    "kernel_registry.py",
    "profiles.py",
    "propagation.py",
    "stitching.py",
}

GRF_REVIEWS = {
    "m0_ports.py": (
        "SNAPSHOT",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "GRF workspace consistent-state adapter",
        "The compatibility adapter implements the public Core state port with deterministic in-memory bytes and same-volume atomic restore; it imports no GRF private implementation.",
    ),
    "relation_field.py": (
        "CORE",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "geometry current-state propagation",
        "Sparse Cell/Coverage/Lateral/Bridge propagation performs linear scans and contains no route table or external relation index; it also imports placement and recall-result contracts.",
    ),
    "field_engine.py": (
        "CORE",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "in-memory geometry occupancy and bridge state",
        "CellStore is Core-like, while FieldEngine directly imports PlacementRecord and RelationField; the file is not a dependency-closed pure Core leaf.",
    ),
    "placement.py": (
        "ACCESS",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "placement decision and record contracts",
        "Dataclasses validate host-provided placement objects; no hash, scoring, keyword, vector, or automatic semantic placement algorithm is present.",
    ),
    "placement_protocol.py": (
        "ACCESS",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "host placement request and decision contracts",
        "Typed host contracts validate explicit LLM/host decisions and depend only on the public geometry address contract.",
    ),
    "recall.py": (
        "CORE",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "bounded geometry-entry recall",
        "Bounded traversal is Core behavior, but the file currently couples RelationField traversal to RecallDigest product records.",
    ),
    "storage.py": (
        "ACCESS",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "file-first evidence, placement, admission, recall, and stitch objects",
        "One store persists multiple ownership domains; it must be split through stable public ports rather than moved as a pure module.",
    ),
    "facade.py": (
        "ACCESS",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "host workflow facade and workspace lifecycle",
        "The facade coordinates Capture, Admission, Recall, Snapshot, Source, and storage responsibilities across module boundaries.",
    ),
    "openclaw_bridge.py": (
        "OPENCLAW",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "OpenClaw command translation",
        "The adapter is host-specific but still imports GRF facade and geometry contracts from the mixed namespace; extraction is pending.",
    ),
    "geometry_storage.py": (
        "ACCESS",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "physical paths for geometry, evidence, admission, and source objects",
        "Path functions mix Core placement locations with Access evidence/source locations and require ownership separation.",
    ),
    "kernel_registry.py": (
        "CORE",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "coverage kernel registry and deterministic compression",
        "Current code depends only on deterministic coverage templates and canonical bytes and owns no product policy.",
    ),
    "replay.py": (
        "SNAPSHOT",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "workspace structural replay",
        "Replay reconstructs geometry from files but also invokes Recall and accesses the mixed GRF store.",
    ),
    "ledger.py": (
        "TRACE",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "append-only operation records",
        "The ledger is an observability record implementation using canonical bytes; Core does not import it.",
    ),
    "evidence.py": (
        "ACCESS",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "raw evidence record contract",
        "The contract preserves UTF-8 source content and explicit source-window references without geometry semantics.",
    ),
    "source_window.py": (
        "ACCESS",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "source window record contract",
        "The contract owns source projection metadata and has no Core implementation dependency.",
    ),
    "capture.py": (
        "ACCESS",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "file-first capture workflow",
        "Capture preserves raw evidence through GRFFileStore and does not perform placement or recall.",
    ),
    "admission.py": (
        "ACCESS",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "minimal admission record contract",
        "The record binds explicit placement identity and contains no placement algorithm.",
    ),
    "admission_bridge.py": (
        "ACCESS",
        "CANDIDATE",
        "SPLIT",
        "MEDIUM",
        "explicit admission workflow",
        "The workflow coordinates Access records, Core geometry contracts, evidence fallback, and the mixed store.",
    ),
    "bridge_kernel.py": (
        "CORE",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "deterministic bridge geometry contract",
        "The immutable bridge contract depends only on fixed-point Core math.",
    ),
    "stitching.py": (
        "CORE",
        "ACTIVE",
        "KEEP",
        "HIGH",
        "deterministic stitch validation contracts",
        "Stitch objects and acceptance checks use BridgeKernel and fixed-point math without host or semantic policy.",
    ),
}

ACCESS_FILES = {
    "contract_evolution.py",
    "evidence_island.py",
    "exporters.py",
    "host_contract.py",
    "importers.py",
    "ingestion.py",
    "local_patch.py",
    "path_encoding.py",
    "real_sources.py",
}


@dataclass(frozen=True)
class Classification:
    owner: str
    lifecycle: str
    action: str
    confidence: str
    role: str
    state: str
    public_api: str
    reason: str
    target_path: str = ""
    migration_status: str = "NOT_APPLICABLE"
    evidence: str = ""
    forbidden_evidence: tuple[dict[str, str], ...] = ()
    review_status: str = "AUTO_CANDIDATE"
    reviewed_at: str = ""
    asset_class: str = ""
    validation_gate: str = ""


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.splitlines()


def module_name(path: str) -> str | None:
    source = PurePosixPath(path)
    if source.suffix != ".py":
        return None
    parts = list(source.parts)
    if parts[:2] == ["reference", "python"]:
        parts = parts[2:]
    elif "src" in parts:
        parts = parts[parts.index("src") + 1 :]
    else:
        parts[-1] = source.stem
        return ".".join(parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = source.stem
    return ".".join(parts)


def imports_for(path: str) -> list[str]:
    source = ROOT / path
    if source.suffix != ".py":
        return []
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=path)
    except (SyntaxError, UnicodeDecodeError):
        return []
    current = module_name(path) or ""
    package = current if path.endswith("/__init__.py") else current.rpartition(".")[0]
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".") if package else []
                keep = max(0, len(parts) - (node.level - 1))
                target = parts[:keep]
                if node.module:
                    target.extend(node.module.split("."))
                if target:
                    imports.add(".".join(target))
            elif node.module:
                imports.add(node.module)
    return sorted(imports)


def active_governance_paths(root: Path = ROOT) -> set[str]:
    basis = root / ACTIVE_BASIS
    text = basis.read_text(encoding="utf-8")
    active = {ACTIVE_BASIS}
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        resolved = (basis.parent / target).resolve()
        try:
            relative = resolved.relative_to(root.resolve()).as_posix()
        except ValueError as error:
            raise ValueError(f"active governance link escapes repository: {target}") from error
        if not resolved.is_file():
            raise ValueError(f"active governance link does not exist: {target}")
        active.add(relative)
    return active


def lab_asset(classification: Classification, asset_class: str, validation_gate: str = "") -> Classification:
    return Classification(
        **{**classification.__dict__, "asset_class": asset_class, "validation_gate": validation_gate}
    )


def classify(path: str, imports: list[str], active_governance: set[str] | None = None) -> Classification:
    p = path.replace("\\", "/")
    name = PurePosixPath(p).name
    active_governance = active_governance or set()
    if p.startswith("packages/") and "/tests/" in p:
        package = p.split("/", 2)[1].removeprefix("nollm-")
        return lab_asset(Classification(
            "LAB", "ACTIVE", "KEEP", "HIGH",
            "package-local independent test", "development-only state", "development",
            "Package tests verify only public dependencies and are not production implementation.",
            evidence=f"Package test path with direct imports {imports}.",
            review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "ACTIVE_TEST", f"package:{package}")
    if p.startswith("packages/nollm-"):
        package = p.split("/", 2)[1].removeprefix("nollm-").upper()
        owner = "DISTRIBUTION" if package == "DISTRIBUTIONS" else package
        return Classification(
            owner,
            "ACTIVE",
            "KEEP",
            "HIGH",
            "module package",
            "module-owned state or public contracts",
            "public" if "/src/" in p else "metadata",
            "Target package asset with explicit package ownership.",
            evidence=f"Path is inside packages/{p.split('/')[1]} and direct imports are {imports}.",
            review_status="DEPENDENCY_REVIEWED",
            reviewed_at=REVIEWED_AT,
        )
    if p.startswith("lab/nollm-lab/history/"):
        return lab_asset(Classification(
            "LAB", "HISTORICAL", "KEEP", "HIGH",
            "legacy reference", "historical reproduction inputs", "none",
            "History-directory Lab assets preserve withdrawn validation routes and are not active tools.",
            evidence="Stable Lab history directory convention.",
            review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "LEGACY_REFERENCE")
    if p.startswith("lab/nollm-lab/openclaw/results/"):
        return lab_asset(Classification(
            "LAB", "HISTORICAL", "KEEP", "HIGH",
            "historical result", "frozen validation output", "none",
            "Recorded model-run results are preserved evidence, not active tools.",
            evidence="Stable Lab results directory convention.",
            review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "HISTORICAL_RESULT")
    if p.startswith("lab/nollm-lab/openclaw/datasets/"):
        return lab_asset(Classification(
            "LAB", "HISTORICAL", "KEEP", "HIGH", "legacy reference",
            "versioned validation dataset", "none",
            "Paused OpenClaw dataset is retained but is not an input to the current final gate.",
            evidence="No current final-gate consumer.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "LEGACY_REFERENCE")
    if p.startswith("lab/nollm-lab/geometry/"):
        active_tools = {
            "generate_compiled_templates.py": "lab:compiled-templates",
            "run_broad_residue_coverage_calibration.py": "lab:broad-residue-calibration",
            "run_safe_writable_field_validation.py": "lab:safe-writable-field",
            "run_dense_locality_surface_validation.py": "lab:dense-locality-surface",
            "run_dense_single_entry_recall_validation.py": "lab:dense-single-entry-recall",
            "run_natural_multi_entry_observation.py": "lab:natural-multi-entry-observation",
        }
        role = "active tool" if name in active_tools else "active library"
        asset_class = "ACTIVE_TOOL" if role == "active tool" else "ACTIVE_LIBRARY"
        gate = active_tools[name] if role == "active tool" else "lab:geometry-parity"
        return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", role, "compile-time geometry definitions", "development", "Current geometry generation and compile support.", evidence="Stable Lab geometry directory convention.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), asset_class, gate)
    if p.startswith("lab/nollm-lab/statement_formation/"):
        gate = "lab:statement-formation-fixtures" if "/fixtures/" in p or name == "evaluate_fixture_decisions.py" else "lab:statement-formation-corpus"
        return lab_asset(Classification("LAB", "MIGRATION_ASSET", "KEEP", "HIGH", "legacy regression", "versioned validation input", "none", "Parser/schema regression asset; it does not establish semantic quality.", evidence="Superseded by the normal-chat live Formation gate.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "LEGACY_REGRESSION", gate)
    if p.startswith("lab/nollm-lab/openclaw_formation/"):
        if name == "validate_live_plugin_evidence.py":
            return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active validation", "validation workspace only", "development", "Read-only verifier for frozen normal-chat plugin evidence.", evidence="Explicit openclaw:formation-live final gate.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_VALIDATION", "openclaw:formation-live")
        return lab_asset(Classification("LAB", "HISTORICAL", "KEEP", "HIGH", "historical result", "frozen validation output", "none", "Prior standalone Formation runs are parser/schema regression evidence, not natural-chat semantic quality.", evidence="Normal-chat gate is authoritative.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "HISTORICAL_RESULT")
    if p.startswith("lab/nollm-lab/dream_agent/"):
        if name in {"verify_live_evidence.py", "run-live-round.ps1"}:
            return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active validation", "validation workspace only", "development", "Read-only replay or explicit live validation entrypoint for the invisible Dream Agent gate.", evidence="Explicit AOLD V3.3 final-gate command.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_VALIDATION", "openclaw:dream-agent-live")
        if "/prompts/" in p:
            return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active library", "versioned prompt definition", "development", "Canonical versioned Dream Formation prompt input.", evidence="AOLD V3.3 prompt authority.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_LIBRARY", "openclaw:dream-agent-live")
        if "/schemas/" in p:
            return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active fixture", "versioned schema definition", "development", "Canonical Dream Formation output schema fixture.", evidence="AOLD V3.3 schema authority.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_FIXTURE", "openclaw:dream-agent-live")
        return lab_asset(Classification("LAB", "HISTORICAL", "KEEP", "HIGH", "historical result", "frozen validation output", "none", "Frozen three-round Dream Agent evidence and reports are replay inputs, not production state.", evidence="AOLD V3.3 final live gate.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "HISTORICAL_RESULT")
    if p.startswith("lab/nollm-lab/m1/"):
        if name == "run_adaptive_surface_validation.py":
            return lab_asset(Classification("LAB", "HISTORICAL", "KEEP", "HIGH", "historical validation", "frozen adaptive Surface checkpoint", "none", "Preserved V3.6 adaptive Surface validator; superseded by the V3.7 physical field validators.", evidence="V3.7 route supersedes the transitional V3.6 Surface contract.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "LEGACY_REFERENCE")
        gates = {
            "run_geometry_parity.py": "lab:geometry-parity",
            "run_core_capability_validation.py": "lab:core-capability",
            "run_m1_minimal_e2e.py": "lab:minimal-e2e",
            "run_adaptive_surface_validation.py": "lab:adaptive-surface",
            "run_rotated_layer0_workspace_migration.py": "lab:rotated-layer0-migration",
            "run_rotated_surface_coarsening_validation.py": "lab:rotated-surface-coarsening",
            "run_translation_covariant_workspace_migration.py": "lab:translation-covariant-migration",
            "run_translation_normalized_workspace_migration.py": "lab:translation-normalized-migration",
            "run_bounded_approximate_workspace_migration.py": "lab:bounded-approximate-migration",
            "seed_translation_covariant_live_fixture.py": "lab:translation-covariant-live",
        }
        return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active validation", "validation workspace only", "development", "Current public-contract validation entrypoint.", evidence="Explicit current final-gate command.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_VALIDATION", gates[name])
    if p == "lab/nollm-lab/recall_lens/run_v311r6_content_neutral_memory_validation.py":
        return lab_asset(Classification(
            "LAB", "ACTIVE", "KEEP", "HIGH", "active validation",
            "validation workspace only", "development",
            "Current content-neutral memory offline Gate A-F validation entrypoint.",
            evidence="Explicit V3.11 Rev6 final-gate command.",
            review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "ACTIVE_VALIDATION", "lab:content-neutral-memory")
    if p in {
        "lab/nollm-lab/recall_lens/run_v311r61_active_pipeline_gate.mjs",
        "lab/nollm-lab/recall_lens/run_v311r61_python_import_gate.py",
        "lab/nollm-lab/recall_lens/run_v311r61_capture_pipeline_validation.mjs",
        "lab/nollm-lab/recall_lens/run_v311r61_offline_validation.py",
    }:
        return lab_asset(Classification(
            "LAB", "ACTIVE", "KEEP", "HIGH", "active validation",
            "validation workspace only", "development",
            "Current single active pipeline reachability and import-graph gate.",
            evidence="Explicit V3.11 Rev6.1 Gate F command.",
            review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "ACTIVE_VALIDATION", "lab:single-active-content-neutral-pipeline")
    if p.startswith("reference/python/tests/m0/"):
        return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active governance test", "development-only state", "development", "Executed by the current M0 governance gate.", evidence="Explicit current final-gate suite reference/python/tests/m0.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_TEST", "governance:m0")
    if p in {
        "reference/python/tests/test_no_forbidden_features.py",
        "reference/python/tests/test_architecture_language.py",
        "reference/python/tests/test_repository_hygiene.py",
    }:
        return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active architecture test", "development-only state", "development", "Executed by the current architecture governance gate.", evidence="Explicit current final-gate test path.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_TEST", "governance:architecture")
    if p.startswith("reference/python/tests/grf/"):
        return lab_asset(Classification("LAB", "MIGRATION_ASSET", "KEEP", "HIGH", "legacy compatibility regression", "development-only state", "development", "Executed only by the explicit GRF compatibility regression gate.", evidence="Explicit current compatibility suite reference/python/tests/grf.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT), "LEGACY_REGRESSION", "compatibility:grf")
    if p.startswith("tools/") and name in {"generate_module_ownership_manifest.py", "validate_module_ownership_manifest.py", "check_module_boundaries.py", "verify_v311r61_single_active_pipeline.py"}:
        gate = "repository:boundary" if name == "check_module_boundaries.py" else "lab:single-active-content-neutral-pipeline" if name == "verify_v311r61_single_active_pipeline.py" else "repository:manifest"
        return lab_asset(Classification("LAB", "ACTIVE", "KEEP", "HIGH", "active repository tool", "governance state", "development", "Current machine-governance entrypoint.", evidence="Explicit current final-gate repository command.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "ACTIVE_REPOSITORY_TOOL", gate)
    if p.startswith("experiments/") and "/results/" in p:
        return lab_asset(Classification("LAB", "HISTORICAL", "KEEP", "HIGH", "historical result", "frozen validation output", "none", "Frozen experiment output is not executable current-gate input.", evidence="Stable experiment results directory convention.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "HISTORICAL_RESULT")
    if p.startswith("validation/") and PurePosixPath(p).suffix.lower() in {".md", ".json"}:
        return lab_asset(Classification("LAB", "HISTORICAL", "KEEP", "HIGH", "historical result", "frozen validation output", "none", "Frozen validation report is not executable current-gate input.", evidence="Validation report extension and no current final-gate command.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT), "HISTORICAL_RESULT")
    if p.startswith(("lab/", "experiments/", "validation/", "reference/python/tests/", "examples/", "tools/")) or p in {"run_tests.py"}:
        return lab_asset(Classification(
            "LAB", "HISTORICAL", "KEEP", "HIGH", "legacy reference",
            "development-only state", "none",
            "Preserved Lab asset is not executed by the current final gate.",
            evidence=f"No current final-gate consumer; direct imports are {imports}.",
            review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT,
        ), "LEGACY_REFERENCE")
    if p.startswith("distributions/"):
        return Classification(
            "DISTRIBUTION",
            "ACTIVE",
            "KEEP",
            "HIGH",
            "composition metadata",
            "none",
            "metadata",
            "Distribution tree contains only composition documentation and JSON manifests.",
            evidence="File is under the machine-enforced distributions metadata root.",
            review_status="DEPENDENCY_REVIEWED",
            reviewed_at=REVIEWED_AT,
        )
    if p in {
        "integrations/openclaw/formation-loop/python/nollm_openclaw_formation/adapter.py",
        "integrations/openclaw/formation-loop/python/nollm_openclaw_formation/dream_adapter.py",
        "integrations/openclaw/formation-loop/python/nollm_openclaw_formation/sculptor.py",
        "integrations/openclaw/formation-loop/python/nollm_openclaw_formation/legacy_bridge.py",
        "integrations/openclaw/formation-loop/python/nollm_openclaw_formation/legacy_cartographer.py",
    }:
        return Classification(
            "OPENCLAW", "MIGRATION_ASSET", "KEEP", "HIGH",
            "offline Formation migration", "none", "none",
            "Rev6.1 isolates this historical contract from every active plugin action and import path.",
            evidence="Reachable only through explicit offline migration modules and tests.",
            review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT,
        )
    if p.startswith("integrations/openclaw/formation-loop/"):
        return Classification(
            "OPENCLAW", "ACTIVE", "KEEP", "HIGH",
            "active OpenClaw Formation integration", "host/plugin state", "public",
            "Normal-chat live gate validates runtime registration, canonical prompt parsing, and Access exact-span results.",
            evidence="Bound to validation_gate openclaw:formation-live.",
            review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT,
        )
    if p.startswith("integrations/openclaw/"):
        return Classification(
            "OPENCLAW",
            "MIGRATION_ASSET",
            "SPLIT",
            "LOW",
            "paused OpenClaw host integration",
            "host/plugin state",
            "none",
            "M1 keeps OpenClaw outside active distributions pending a future E2E task.",
            migration_status="BLOCKED_BY_SPLIT",
            evidence=f"Paused migration path with direct imports {imports}.",
        )
    if p.startswith("reference/python/nollm/grf/"):
        return Classification(
            "LEGACY", "MIGRATION_ASSET", "QUARANTINE", "LOW",
            "GRF compatibility and migration implementation",
            "historical mixed Core/Access/Snapshot/Trace state", "none",
            "M1 package implementations are active; GRF remains a tested compatibility baseline outside Bare/Minimal.",
            migration_status="QUARANTINED",
            evidence=f"Legacy GRF path retained for migration regression with direct imports {imports}.",
            review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT,
        )
    if p.startswith("legacy/") or p.startswith("reference/python/nollm/dream_geometry/"):
        return Classification(
            "LEGACY",
            "MIGRATION_ASSET",
            "QUARANTINE",
            "LOW",
            "historical migration asset",
            "historical or mixed state",
            "none",
            "Preserved for migration evidence; current ownership is not dependency-closed.",
            migration_status="QUARANTINED",
            evidence=f"Historical path with direct imports {imports}.",
        )
    if p.startswith("protocol/"):
        return Classification(
            "ACCESS",
            "MIGRATION_ASSET",
            "SPLIT",
            "MEDIUM",
            "historical wire contracts",
            "mixed protocol state",
            "candidate",
            "Protocol assets require M1 contract extraction under the modular architecture.",
            migration_status="BLOCKED_BY_SPLIT",
            evidence="Historical V2 protocol path retained as superseded migration input.",
        )
    if p in active_governance:
        return Classification("DISTRIBUTION", "ACTIVE", "KEEP", "HIGH", "active repository governance", "none", "governance", "Linked from the single active project basis.", evidence=f"Resolved from {ACTIVE_BASIS}.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT)
    if p.startswith("docs/architecture/modules/"):
        charter_owner = name.removeprefix("NOLLM_").removesuffix("_CHARTER.md")
        owner = charter_owner if charter_owner in {"CORE", "SNAPSHOT", "TRACE", "ACCESS", "HISTORY", "AUDIT", "OPENCLAW", "LAB", "DISTRIBUTIONS"} else "DISTRIBUTION"
        if owner == "DISTRIBUTIONS":
            owner = "DISTRIBUTION"
        classification = Classification(owner, "ACTIVE", "KEEP", "HIGH", "module charter", "none", "governance", "Current M0 module charter.", evidence="Explicit current charter path.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT)
        if owner == "LAB":
            return lab_asset(classification, "ACTIVE_FIXTURE", "repository:manifest")
        return classification
    if p.startswith("docs/architecture/module-ownership/"):
        return Classification("DISTRIBUTION", "GENERATED", "KEEP", "HIGH", "ownership governance", "none", "governance", "Generated ownership or boundary record.", evidence="Generated by reviewed repository tooling.", review_status="DEPENDENCY_REVIEWED", reviewed_at=REVIEWED_AT)
    if p in {
        "AGENTS.md",
        "README.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md",
        "docs/project/AOLD_SINGLE_CONTENT_NEUTRAL_PIPELINE_REPORT.md",
    }:
        return Classification("DISTRIBUTION", "ACTIVE", "KEEP", "HIGH", "stable repository governance", "none", "governance", "Stable repository navigation or first-principles authority.", evidence="Exact stable governance path.", review_status="CODE_REVIEWED", reviewed_at=REVIEWED_AT)
    if p.startswith("docs/"):
        return Classification("LEGACY", "HISTORICAL", "KEEP", "MEDIUM", "historical documentation", "none", "none", "Preserved historical or superseded documentation.", evidence="Documentation is outside current M0C1 governance paths.")
    if p.startswith("integrations/"):
        return Classification("OPENCLAW", "MIGRATION_ASSET", "SPLIT", "MEDIUM", "host adapter migration asset", "host state", "candidate", "Integration requires module extraction review.", migration_status="BLOCKED_BY_SPLIT", evidence=f"Integration path with direct imports {imports}.")
    return Classification(
        "LEGACY",
        "MIGRATION_ASSET",
        "QUARANTINE",
        "LOW",
        "unresolved migration asset",
        "unknown or mixed",
        "none",
        "Catch-all classification is intentionally conservative and cannot become ACTIVE/HIGH.",
        migration_status="QUARANTINED",
        evidence=f"Unmatched path; direct imports are {imports}.",
    )


def build_rows(paths: list[str]) -> tuple[list[dict[str, object]], list[str]]:
    active_governance = active_governance_paths()
    import_map = {path: imports_for(path) for path in paths}
    module_index = {name: path for path in paths if (name := module_name(path))}
    reverse: dict[str, set[str]] = {path: set() for path in paths}
    for source, imports in import_map.items():
        for imported in imports:
            parts = imported.split(".")
            for length in range(len(parts), 0, -1):
                target = module_index.get(".".join(parts[:length]))
                if target:
                    reverse[target].add(source)
                    break
    rows: list[dict[str, object]] = []
    classified: set[str] = set()
    for path in paths:
        item = classify(path, import_map[path], active_governance)
        classified.add(path)
        suffix = PurePosixPath(path).suffix.lower().lstrip(".") or "none"
        rows.append(
            {
                "path": path,
                "file_type": suffix,
                "current_namespace": str(PurePosixPath(path).parent),
                "owner": item.owner,
                "secondary_owner": "",
                "lifecycle_status": item.lifecycle,
                "asset_class": item.asset_class,
                "validation_gate": item.validation_gate,
                "runtime_role": item.role,
                "owned_state": item.state,
                "public_api": item.public_api,
                "imports": import_map[path],
                "imported_by": sorted(reverse[path]),
                "migration_action": item.action,
                "confidence": item.confidence,
                "reason": item.reason,
                "target_path": item.target_path,
                "migration_status": item.migration_status,
                "classification_evidence": item.evidence,
                "forbidden_feature_evidence": list(item.forbidden_evidence),
                "review_status": item.review_status,
                "reviewed_at": item.reviewed_at,
            }
        )
    return rows, sorted(set(paths) - classified)


def render(rows: list[dict[str, object]], unclassified: list[str]) -> dict[Path, bytes]:
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        encoded = dict(row)
        for field in ("imports", "imported_by", "forbidden_feature_evidence"):
            encoded[field] = json.dumps(encoded[field], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        writer.writerow(encoded)
    return {
        MANIFEST_CSV: csv_buffer.getvalue().encode("utf-8"),
        MANIFEST_JSON: (json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        UNCLASSIFIED: (("\n".join(unclassified) + "\n") if unclassified else "").encode("utf-8"),
    }


def write_outputs(outputs: dict[Path, bytes]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path, payload in outputs.items():
        path.write_bytes(payload)


def check_outputs(outputs: dict[Path, bytes]) -> list[str]:
    mismatches = []
    for path, expected in outputs.items():
        if not path.exists() or path.read_bytes() != expected:
            mismatches.append(path.relative_to(ROOT).as_posix())
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write canonical V2 manifest outputs")
    mode.add_argument("--check", action="store_true", help="verify outputs without writing")
    args = parser.parse_args()
    paths = tracked_files()
    rows, unclassified = build_rows(paths)
    outputs = render(rows, unclassified)
    if args.write:
        write_outputs(outputs)
        print(f"classified {len(rows)} tracked files; unclassified={len(unclassified)}")
        return 0
    mismatches = check_outputs(outputs)
    if mismatches:
        print("ownership manifest differs: " + ", ".join(mismatches), file=sys.stderr)
        return 1
    print(f"ownership manifest check: tracked={len(rows)} unclassified={len(unclassified)} unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
