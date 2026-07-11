"""Check tracked Python and TypeScript sources against the M0 ownership model."""

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
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "module-boundaries.json"
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".cjs"}
TS_IMPORT_RE = re.compile(
    r"(?:from\s+|import\s*\(\s*|require\s*\(\s*)[\"']([^\"']+)",
)


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
        identity = "\0".join(
            (self.kind, self.path, self.source_owner, self.target_owner, self.target)
        )
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()


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
    parts = list(source.parts)
    if source.suffix != ".py":
        return None
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
    source_path = ROOT / path
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=path)
    current = module_name(path) or ""
    package = current if path.endswith("/__init__.py") else current.rpartition(".")[0]
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package_parts = package.split(".") if package else []
                keep = max(0, len(package_parts) - (node.level - 1))
                prefix = package_parts[:keep]
                if node.module:
                    prefix.extend(node.module.split("."))
                imports.append(".".join(prefix))
            elif node.module:
                imports.append(node.module)
    return sorted(set(filter(None, imports)))


def resolve_python(import_name: str, modules: dict[str, str]) -> str | None:
    parts = import_name.split(".")
    for length in range(len(parts), 0, -1):
        candidate = ".".join(parts[:length])
        if candidate in modules:
            return modules[candidate]
    return None


def resolve_relative_source(source: str, imported: str, tracked: set[str]) -> str | None:
    base = PurePosixPath(source).parent.joinpath(imported)
    candidates = [
        str(base.with_suffix(suffix)) for suffix in SOURCE_SUFFIXES
    ] + [
        str(base / ("index" + suffix)) for suffix in SOURCE_SUFFIXES
    ]
    for candidate in candidates:
        normalized = PurePosixPath(candidate).as_posix()
        while normalized.startswith("../"):
            normalized = normalized[3:]
        if normalized in tracked:
            return normalized
    return None


def is_private_target(import_name: str, target_path: str) -> bool:
    parts = import_name.replace("-", "_").split(".")[1:]
    return any(part.startswith("_") for part in parts) or "/private/" in target_path


def has_distribution_logic(path: str) -> bool:
    if Path(path).suffix != ".py":
        return True
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    for index, node in enumerate(tree.body):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            continue
        return True
    return False


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    active: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
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
                components.append(sorted(component))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(components)


def collect_findings(
    config: dict[str, object],
    paths: list[str],
    manifest: dict[str, dict[str, str]],
) -> tuple[list[Finding], list[list[str]], dict[str, list[str]]]:
    tracked = set(paths)
    modules = {
        name: path
        for path in paths
        if (name := module_name(path))
    }
    graph = {name: set() for name in config["modules"]}
    findings: dict[str, Finding] = {}

    def add(
        kind: str,
        source: str,
        source_owner: str,
        target_owner: str,
        target: str,
        detail: str,
    ) -> None:
        record = manifest[source]
        finding = Finding(
            kind=kind,
            path=source,
            source_owner=source_owner,
            target_owner=target_owner,
            target=target,
            detail=detail,
            migration_action=record["migration_action"],
            confidence=record["confidence"],
        )
        findings[finding.fingerprint] = finding

    for path in paths:
        if Path(path).suffix not in SOURCE_SUFFIXES:
            continue
        source = manifest[path]
        source_owner = source["owner"]
        if source_owner == "DISTRIBUTION" and path.startswith("distributions/"):
            if has_distribution_logic(path):
                add(
                    "distribution_business_logic",
                    path,
                    source_owner,
                    source_owner,
                    path,
                    "Distributions may contain composition metadata only.",
                )
        if Path(path).suffix == ".py":
            imports: Iterable[str] = python_imports(path)
        else:
            text = (ROOT / path).read_text(encoding="utf-8")
            imports = sorted(set(TS_IMPORT_RE.findall(text)))
        for imported in imports:
            target_path: str | None = None
            target_owner: str | None = None
            if Path(path).suffix == ".py":
                target_path = resolve_python(imported, modules)
                if target_path:
                    target_owner = manifest[target_path]["owner"]
                else:
                    top_level = imported.split(".")[0]
                    target_owner = config["python_packages"].get(top_level)
            elif imported.startswith("."):
                target_path = resolve_relative_source(path, imported, tracked)
                if target_path:
                    target_owner = manifest[target_path]["owner"]
            else:
                for package, owner in config["typescript_packages"].items():
                    if imported == package or imported.startswith(package + "/"):
                        target_owner = owner
                        break
            if not target_owner or target_owner == source_owner:
                continue
            target_label = target_path or imported
            if source_owner in graph and target_owner in graph:
                graph[source_owner].add(target_owner)
            if source_owner not in config["modules"]:
                continue
            allowed = config["modules"][source_owner]["allowed"]
            if target_owner == "LAB" and source_owner not in {"LAB", "LEGACY"}:
                add(
                    "production_imports_lab",
                    path,
                    source_owner,
                    target_owner,
                    target_label,
                    f"{source_owner} production code imports LAB.",
                )
            elif target_owner not in allowed:
                add(
                    "forbidden_module_import",
                    path,
                    source_owner,
                    target_owner,
                    target_label,
                    f"{source_owner} may depend only on {allowed}.",
                )
            if (
                source_owner == "OPENCLAW"
                and target_owner == "CORE"
                and is_private_target(imported, target_label)
            ):
                add(
                    "openclaw_imports_core_private",
                    path,
                    source_owner,
                    target_owner,
                    target_label,
                    "OpenClaw may not import Core private implementation.",
                )

    cycles = strongly_connected_components(graph)
    graph_report = {name: sorted(targets) for name, targets in graph.items()}
    return sorted(findings.values(), key=lambda item: item.fingerprint), cycles, graph_report


def make_report(
    paths: list[str],
    findings: list[Finding],
    cycles: list[list[str]],
    graph: dict[str, list[str]],
) -> dict[str, object]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    records = []
    for finding in findings:
        record = asdict(finding)
        record["fingerprint"] = finding.fingerprint
        record["disposition"] = "M1 extraction or removal; no M0 semantic rewrite"
        records.append(record)
    return {
        "schema_version": 1,
        "generated_from_head": head,
        "tracked_file_count": len(paths),
        "violations": records,
        "cycles": cycles,
        "graph": graph,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="replace the reviewed M0 baseline with current findings",
    )
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest_path = ROOT / config["manifest"]
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = {row["path"]: row for row in rows}
    paths = tracked_files()
    missing = sorted(set(paths) - set(manifest))
    stale = sorted(set(manifest) - set(paths))
    if missing or stale:
        print(
            f"ownership manifest is stale: missing={len(missing)} stale={len(stale)}",
            file=sys.stderr,
        )
        return 2
    try:
        findings, cycles, graph = collect_findings(config, paths, manifest)
    except (SyntaxError, UnicodeDecodeError) as error:
        print(f"source scan failed: {error}", file=sys.stderr)
        return 2
    report = make_report(paths, findings, cycles, graph)
    baseline_path = ROOT / config["baseline"]
    if args.write_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"module boundary baseline written: violations={len(findings)} "
            f"cycles={len(cycles)}"
        )
        return 0
    if not baseline_path.exists():
        print("boundary baseline is missing; run with --write-baseline", file=sys.stderr)
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    expected = {item["fingerprint"] for item in baseline["violations"]}
    actual = {finding.fingerprint for finding in findings}
    new_findings = actual - expected
    new_cycles = [cycle for cycle in cycles if cycle not in baseline["cycles"]]
    print(
        f"module boundaries: current={len(actual)} baseline={len(expected)} "
        f"new={len(new_findings)} resolved={len(expected - actual)} "
        f"cycles={len(cycles)} new_cycles={len(new_cycles)}"
    )
    return 1 if new_findings or new_cycles else 0


if __name__ == "__main__":
    sys.exit(main())
