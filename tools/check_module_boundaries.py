"""Report production and migration dependencies against M0C1 ownership rules."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "module-boundaries.json"
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".cjs"}
PRODUCTION_OWNERS = {"CORE", "SNAPSHOT", "TRACE", "ACCESS", "HISTORY", "AUDIT", "OPENCLAW"}
TS_IMPORT_RE = re.compile(r"(?:from\s+|import\s*\(\s*|require\s*\(\s*)[\"']([^\"']+)")


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    source_owner: str
    target_owner: str
    target: str
    detail: str
    migration_action: str
    confidence: str

    @property
    def fingerprint(self) -> str:
        value = "\0".join((self.kind, self.path, self.source_owner, self.target_owner, self.target))
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
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


def python_imports(path: str) -> list[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    current = module_name(path) or ""
    package = current if path.endswith("/__init__.py") else current.rpartition(".")[0]
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".") if package else []
                keep = max(0, len(parts) - (node.level - 1))
                target = parts[:keep]
                if node.module:
                    target.extend(node.module.split("."))
                if target:
                    values.add(".".join(target))
            elif node.module:
                values.add(node.module)
    return sorted(values)


def resolve_python(imported: str, modules: dict[str, str]) -> str | None:
    parts = imported.split(".")
    for length in range(len(parts), 0, -1):
        target = modules.get(".".join(parts[:length]))
        if target:
            return target
    return None


def resolve_relative_source(source: str, imported: str, tracked: set[str]) -> str | None:
    base = PurePosixPath(source).parent.joinpath(imported)
    candidates = [str(base.with_suffix(suffix)) for suffix in SOURCE_SUFFIXES]
    candidates.extend(str(base / ("index" + suffix)) for suffix in SOURCE_SUFFIXES)
    for candidate in candidates:
        normalized = PurePosixPath(candidate).as_posix()
        if normalized in tracked:
            return normalized
    return None


def is_private(imported: str, target: str) -> bool:
    return any(part.startswith("_") for part in imported.split(".")[1:]) or "/private/" in target


def distribution_has_logic(path: str) -> bool:
    if Path(path).suffix != ".py":
        return True
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    for index, node in enumerate(tree.body):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            continue
        return True
    return False


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    active: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    output: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        active.add(node)
        for target in sorted(graph.get(node, set())):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in active:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                target = stack.pop()
                active.remove(target)
                component.append(target)
                if target == node:
                    break
            if len(component) > 1:
                output.append(sorted(component))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(output)


def collect_report(config: dict[str, object], rows: list[dict[str, object]], paths: list[str]) -> dict[str, object]:
    by_path = {str(row["path"]): row for row in rows}
    tracked = set(paths)
    modules = {name: path for path in paths if (name := module_name(path))}
    production_graph = {owner: set() for owner in PRODUCTION_OWNERS}
    all_graph = {owner: set() for owner in set(config["modules"]) | {"LEGACY"}}
    production: dict[str, Finding] = {}
    migration: dict[str, Finding] = {}
    compatibility: list[dict[str, str]] = []

    def add(target: dict[str, Finding], kind: str, path: str, target_owner: str, target_path: str, detail: str) -> None:
        row = by_path[path]
        finding = Finding(
            kind,
            path,
            str(row["owner"]),
            target_owner,
            target_path,
            detail,
            str(row["migration_action"]),
            str(row["confidence"]),
        )
        target[finding.fingerprint] = finding

    for path in paths:
        suffix = Path(path).suffix
        if suffix not in SOURCE_SUFFIXES:
            continue
        row = by_path[path]
        source_owner = str(row["owner"])
        if source_owner == "DISTRIBUTION" and path.startswith("distributions/") and distribution_has_logic(path):
            add(production, "distribution_business_logic", path, source_owner, path, "Distributions may contain composition metadata only.")
        if suffix == ".py":
            imports = python_imports(path)
        else:
            imports = sorted(set(TS_IMPORT_RE.findall((ROOT / path).read_text(encoding="utf-8"))))
        for imported in imports:
            target_path: str | None = None
            target_owner: str | None = None
            if suffix == ".py":
                target_path = resolve_python(imported, modules)
                if target_path:
                    target_owner = str(by_path[target_path]["owner"])
                else:
                    target_owner = config["python_packages"].get(imported.split(".")[0])
            elif imported.startswith("."):
                target_path = resolve_relative_source(path, imported, tracked)
                if target_path:
                    target_owner = str(by_path[target_path]["owner"])
            else:
                for package, owner in config["typescript_packages"].items():
                    if imported == package or imported.startswith(package + "/"):
                        target_owner = owner
                        break
            if not target_owner or target_owner == source_owner:
                continue
            target_label = target_path or imported
            if source_owner in all_graph and target_owner in all_graph and source_owner != "LAB":
                all_graph[source_owner].add(target_owner)
            if source_owner in production_graph and target_owner in production_graph:
                production_graph[source_owner].add(target_owner)

            if source_owner == "LAB":
                continue
            if source_owner == "LEGACY":
                add(migration, "legacy_dependency", path, target_owner, target_label, "Legacy migration asset dependency; excluded from production gate.")
                continue
            if source_owner == "DISTRIBUTION":
                continue
            if source_owner not in PRODUCTION_OWNERS:
                continue
            allowed = set(config["modules"][source_owner]["allowed"])
            if target_owner == "LAB":
                add(production, "production_imports_lab", path, target_owner, target_label, "Production modules may not import Lab.")
            elif target_owner not in allowed:
                add(production, "forbidden_module_import", path, target_owner, target_label, f"{source_owner} may depend only on {sorted(allowed)}.")
            if source_owner == "OPENCLAW" and target_owner == "CORE" and is_private(imported, target_label):
                add(production, "openclaw_imports_core_private", path, target_owner, target_label, "OpenClaw may not import Core private implementation.")

    compat_path = ROOT / "packages" / "COMPATIBILITY_REEXPORTS.md"
    if compat_path.exists():
        for line in compat_path.read_text(encoding="utf-8").splitlines():
            if "->" in line:
                compatibility.append({"declaration": line.strip()})

    def records(values: dict[str, Finding]) -> list[dict[str, object]]:
        result = []
        for finding in sorted(values.values(), key=lambda item: item.fingerprint):
            record = asdict(finding)
            record["fingerprint"] = finding.fingerprint
            record["m1_action"] = "extract mixed responsibilities through public module contracts"
            result.append(record)
        return result

    return {
        "schema_version": 2,
        "tracked_file_count": len(paths),
        "production_violations": records(production),
        "migration_violations": records(migration),
        "compatibility_reexports": compatibility,
        "cycles_production": strongly_connected_components(production_graph),
        "cycles_all": strongly_connected_components(all_graph),
        "graph_production": {key: sorted(value) for key, value in production_graph.items()},
        "graph_all": {key: sorted(value) for key, value in all_graph.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", type=Path, help="write a temporary report without changing the baseline")
    mode.add_argument("--write-baseline", action="store_true", help="write the reviewed production baseline")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest_path = ROOT / config["manifest"]
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = tracked_files()
    manifest_paths = {str(row["path"]) for row in rows}
    if manifest_paths != set(paths):
        print("ownership manifest is stale; run generator --write first", file=sys.stderr)
        return 2
    report = collect_report(config, rows, paths)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    baseline_path = ROOT / config["baseline"]
    if args.report:
        target = args.report if args.report.is_absolute() else ROOT / args.report
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
        print(f"temporary boundary report written: production={len(report['production_violations'])} migration={len(report['migration_violations'])}")
        return 0
    if args.write_baseline:
        baseline_path.write_text(payload, encoding="utf-8")
        print(f"reviewed boundary baseline written: production={len(report['production_violations'])} cycles={len(report['cycles_production'])}")
        return 0
    if not baseline_path.exists():
        print("boundary baseline is missing", file=sys.stderr)
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baseline.get("schema_version") != 2:
        print("boundary baseline requires reviewed schema version 2", file=sys.stderr)
        return 2
    expected = {item["fingerprint"] for item in baseline["production_violations"]}
    actual = {item["fingerprint"] for item in report["production_violations"]}
    new_cycles = [cycle for cycle in report["cycles_production"] if cycle not in baseline["cycles_production"]]
    print(
        f"module boundaries: production={len(actual)} baseline={len(expected)} "
        f"new_production={len(actual - expected)} resolved={len(expected - actual)} "
        f"production_cycles={len(report['cycles_production'])} new_cycles={len(new_cycles)} "
        f"migration={len(report['migration_violations'])}"
    )
    return 1 if actual - expected or new_cycles else 0


if __name__ == "__main__":
    sys.exit(main())
