import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[4]


def test_active_lab_entrypoints_import_cleanly() -> None:
    rows = json.loads((ROOT / "docs/architecture/module-ownership/MODULE_OWNERSHIP_MANIFEST.json").read_text(encoding="utf-8"))
    paths = [ROOT / str(row["path"]) for row in rows if str(row["path"]).startswith("lab/nollm-lab/") and row["owner"] == "LAB" and row["lifecycle_status"] == "ACTIVE" and row["file_type"] == "py"]
    before = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True)
    code = "import importlib.util,sys; p=sys.argv[1]; sys.path[:0]=[str(__import__('pathlib').Path(p).parent),sys.argv[2]]; s=importlib.util.spec_from_file_location('lab_smoke_'+str(abs(hash(p))),p); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)"
    package_paths = [
        ROOT / "packages/nollm-core/src",
        ROOT / "packages/nollm-snapshot/src",
        ROOT / "packages/nollm-trace/src",
        ROOT / "packages/nollm-access/src",
        ROOT / "reference/python",
    ]
    existing_pythonpath = os.environ.get("PYTHONPATH")
    pythonpath = os.pathsep.join(str(path) for path in package_paths)
    if existing_pythonpath:
        pythonpath = os.pathsep.join((pythonpath, existing_pythonpath))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=pythonpath)
    geometry = str(ROOT / "lab/nollm-lab/geometry")
    for path in paths:
        subprocess.run([sys.executable, "-c", code, str(path), geometry], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    after = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True)
    assert after == before
