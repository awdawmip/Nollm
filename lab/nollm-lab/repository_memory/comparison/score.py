"""Score a prepared trial and save its auditable patch, reads and test results."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

from compare import HERE


REQUIRED = {
    "digest": ["packages/nollm-core/src/nollm_core/state.py",
               "packages/nollm-access/src/nollm_access/runtime.py",
               "docs/architecture/module-ownership/CORE_PUBLIC_API_ALLOWLIST.json"],
    "binding": ["packages/nollm-access/src/nollm_access/handle_store.py",
                "packages/nollm-access/src/nollm_access/runtime.py"],
    "statement": ["packages/nollm-access/src/nollm_access/statement.py",
                  "packages/nollm-access/src/nollm_access/statement_store.py"],
}
REGRESSIONS = {
    "digest": ["field_encounter"],
    "binding": ["binding_store_invariants", "access_evidence_resolution", "access_rejects_closed_core",
                "access_memory_loop"],
    "statement": ["memory_statement_strict_types", "evidence_store_canonical_bytes",
                  "evidence_store_immutability", "reuse_validates_canonical_evidence"],
}


def test_result(tree, tests):
    paths = [str(p) for p in sorted((tree / "packages").glob("*/src"))]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(paths), "PYTHONDONTWRITEBYTECODE": "1",
           "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    with TemporaryDirectory() as temp:
        junit = Path(temp) / "result.xml"
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                               "--junitxml", str(junit), *tests], cwd=tree, capture_output=True,
                              env=env, text=True)
        if proc.returncode not in (0, 1) or not junit.exists():
            raise RuntimeError(f"pytest could not score trial: {proc.stdout}\n{proc.stderr}")
        cases = list(ET.parse(junit).iter("testcase"))
        failures = [case.attrib["name"] for case in cases
                    if any(node.tag in {"failure", "error", "skipped"} for node in case)]
        return {"passed": len(cases) - len(failures), "total": len(cases), "unsuccessful": failures}


def check_code(tree, task):
    acceptance = test_result(tree, [str(HERE / "acceptance.py"), "-k", task])
    paths = [f"packages/nollm-access/tests/test_{test}.py" for test in REGRESSIONS[task]]
    if task == "digest":
        paths.extend(["packages/nollm-core/tests/test_core_public_api_allowlist.py",
                      "packages/nollm-snapshot/tests/test_core_snapshot.py"])
    regressions = test_result(tree, paths)
    return {"acceptance": acceptance, "regressions": regressions}


def token_counts(texts):
    # Tokenize each delivered response separately, including repeated reads.
    script = """
    const fs = require('fs');
    const {encode} = require('gpt-tokenizer/encoding/o200k_base');
    const input = JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(input.map(text => encode(text).length)));
    """
    proc = subprocess.run(["node", "-e", script], input=json.dumps(texts), text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError("token counting needs Node and gpt-tokenizer@3.4.0 on NODE_PATH:\n" + proc.stderr)
    return json.loads(proc.stdout)


def provider_usage(trial):
    path = trial / "usage.json"
    if not path.exists():
        return None
    usage = json.loads(path.read_text())
    if type(usage) is not dict or not isinstance(usage.get("model"), str) or not usage["model"]:
        raise ValueError("provider usage requires the observed model name")
    for key in ("input_tokens", "output_tokens"):
        if type(usage.get(key)) is not int or usage[key] < 0:
            raise ValueError(f"provider usage requires a nonnegative {key}")
    return usage


def score(trial):
    spec = json.loads((trial / "trial.json").read_text())
    task = spec["task"]
    tree = trial / "tree"
    events = [json.loads(line) for line in (trial / "trace.jsonl").read_text().splitlines()]
    if not events or events[0]["args"]["command"] != "start":
        raise ValueError("participant did not read starting packet")
    traces = []
    counts = token_counts([event["text"] for event in events])
    for event, count in zip(events, counts, strict=True):
        text = event["text"].encode()
        traces.append({**event["args"], "bytes": len(text), "tokens": count, "sha256": sha256(text).hexdigest()})
    read = {row["path"] for row in traces if row["command"] == "read"}
    cited = json.loads((trial / "evidence.json").read_text())
    if not isinstance(cited, list) or any(type(p) is not str for p in cited) or len(cited) != len(set(cited)):
        raise ValueError("evidence must be an array of distinct paths")
    required = set(REQUIRED[task])
    hits = set(cited) & read & required
    tests = check_code(tree, task)
    return {
        **spec, **tests,
        "success": all(r["total"] > 0 and r["passed"] == r["total"] for r in tests.values()),
        "required_files": sorted(required), "cited_files": sorted(cited),
        "read_and_cited_required_files": len(hits),
        "evidence_recall": len(hits) / len(required),
        "evidence_precision": len(hits) / len(cited) if cited else 0,
        "tokens_encoding": "o200k_base", "initial_tokens": counts[0], "observed_tokens": sum(counts),
        "provider_usage": provider_usage(trial), "trace": traces,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    tree = args.trial.resolve() / "tree"
    # All benchmark changes extend existing modules. Refuse to silently omit untracked work.
    untracked = subprocess.check_output(["git", "-C", tree, "ls-files", "--others", "--exclude-standard"])
    if untracked:
        parser.error("untracked files in candidate tree; stage intentional source additions: " + untracked.decode())
    paths = subprocess.check_output(["git", "-C", tree, "diff", "--name-only", "HEAD"]).decode().splitlines()
    def permitted(path):
        return (path.startswith("packages/") and "/src/" in path) or path in REQUIRED["digest"]
    if not paths or not all(permitted(path) for path in paths):
        parser.error("candidate may edit package source and the governed Core public API document")
    result = score(args.trial.resolve())
    args.out.mkdir(parents=True, exist_ok=True)
    patch = subprocess.check_output(["git", "-C", tree, "diff", "--binary", "HEAD"])
    (args.out / "candidate.patch").write_bytes(patch)
    result["patch_sha256"] = sha256(patch).hexdigest()
    (args.out / "score.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("task", "arm", "success", "evidence_recall", "observed_tokens")}))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
